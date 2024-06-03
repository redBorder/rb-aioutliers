# Copyright (C) 2023 Eneo Tecnologia S.L.
#
# Authors:
# Miguel Álvarez Adsuara <malvarez@redborder.com>
# Pablo Rodriguez Flores <prodriguez@redborder.com>
#
# This program is free software: you can redistribute it and/or modify it under the terms of the
# GNU Affero General Public License as published by the Free Software Foundation, either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along with this program.
# If not, see <https://www.gnu.org/licenses/>.

# Because distributed systems are a zoo......

import threading, time, asyncpg, asyncio
from kazoo.client import KazooClient
from kazoo.recipe.election import Election
from resources.src.redborder.s3 import S3
from resources.src.server.rest import config
from resources.src.logger.logger import logger
from resources.src.redborder.async_jobs.train_job import RbOutlierTrainJob

class RbOutliersZooSync:
    # Please, dont touch or you will break things
    # Make sure you know what you are doing here LMAO
    # atte: Malvads :) <3

    # The leader election happens in rb-aioutliers/leader

    # Master node will do the sync with the webui saved filters
    # That are marked for training with postregsql
    # Also it will do the sync with ZooKeeper for init the starter lock path (rb-aioutliers/{node})
    # of the models

    # Followers nodes will traing the sensors (only flow) with the saved filters
    # When they get a znode without lock it will lock it in
    # ZooKeeper (rb-aioutliers/{node}/lock), making it in-accesible
    # for other nodes, when training finish or service dies the lock is released
    # (ephemeral znode/ rmr (rb-aioutliers/{node}/lock))
    # and it upload to s3 (if alive)

    RB_AIOUTLIERS_MAX_SLEEP = 1e3

    def __init__(self) -> None:
        """
        Initialize the RbAioutliersZoo class.

        Establishes connection to Zookeeper, sets up necessary paths, and initializes S3 client.
        """
        self.zookeeper = KazooClient(
            hosts=config.get("ZooKeeper", "zk_hosts")
        )
        self.zk_sync_path = config.get("ZooKeeper", "zk_path")
        self.s3_client = None
        self.im_master = False
        self.election = None

    def sync_nodes(self):
        """
        Syncronize all rb-aioutliers nodes across the redborder cluster (2 nodes minium to train (master/follower))
        """
        self.setup_s3()
        self.zookeeper.start()
        self.ensure_paths()

    def setup_s3(self):
        """
        Set up the S3 client with configurations from the server.

        Configures the S3 client using AWS credentials and region from the server configuration.
        """
        self.s3_client = S3(
            config.get("AWS", "s3_public_key"),
            config.get("AWS", "s3_private_key"),
            config.get("AWS", "s3_region"),
            config.get("AWS", "s3_bucket"),
            config.get("AWS", "s3_hostname")
        )
    
    def locks_models_on_zoo(self):
        """
        Locks models in Zookeeper if the instance is elected as the master.

        Deletes locks on other models and creates locks on models to be trained.
        """
        if self.im_master:
            children = self.zookeeper.get_children(self.zk_sync_path)
            for child in children:
                if child != "leader":
                    self.zookeeper.delete(self.zk_sync_path + "/" + child, recursive=True)

            models = self.s3_client.list_objects_in_folder("rbaioutliers/latest")
            for model in models:
                if ".ini" in model:
                    model = model.replace('.ini', '')
                    # Persistent Znode
                    self.zookeeper.ensure_path(self.zk_sync_path + "/" + model)
        
    def ensure_paths(self):
        """
        Ensure necessary paths exist in Zookeeper.

        Ensures that the required paths for the application exist in Zookeeper.
        """
        self.zookeeper.ensure_path("/rb-aioutliers")
        self.setup_election()
    
    def is_leader_elected(self):
        """
        Check if a leader is elected in Zookeeper.

        Returns:
            bool: True if a leader exists, False otherwise.
        """
        leader_path = self.zk_sync_path + "/leader"
        leader_exists = self.zookeeper.exists(leader_path)
        if leader_exists:
            leader_children = self.zookeeper.get_children(leader_path)
            if len(leader_children) > 0:
                return True 
            else:
                return False
        
    def setup_election(self):
        """
        Set up leader election in Zookeeper.

        Initializes leader election and starts a thread to monitor the election status.
        """
        self.election = Election(self.zookeeper, self.zk_sync_path + "/leader")
        election_thread = threading.Thread(target=self.election.run, args=(self.election_callback,))
        election_thread.start()
        self.follower_tasks()

    def elect_model_to_train(self):
        """
        Elect a model to be trained.

        Returns:
            str: The name of the model to be trained.
        """
        znodes = self.zookeeper.get_children("rb-aioutliers/")
        for znode in znodes:
            if znode != "leader":
                lock_path = self.zk_sync_path + "/" + znode + "/lock"
                if not self.zookeeper.exists(lock_path):
                    self.zookeeper.create(lock_path, ephemeral=True)
                    return znode
                
    def release_model_lock(self, model):
        """
        Release the lock on a trained model.

        Args:
            model (str): The name of the model to release the lock for.
        """
        lock_path =  self.zk_sync_path + "/" + model + "/lock"
        if self.zookeeper.exists(lock_path):
            self.zookeeper.delete(lock_path)

    def follower_tasks(self):
        """
        Tasks to be performed by followers.

        Continuously monitors for leader election and executes model training tasks if necessary.
        """
        while True:
            if self.is_leader_elected() and not self.im_master:
                model = self.elect_model_to_train()
                if model != None:
                    outlier_job = RbOutlierTrainJob()
                    outlier_job.train_job(model)
                    self.release_model_lock(model)
                time.sleep(self.RB_AIOUTLIERS_MAX_SLEEP)

    def election_callback(self, lock=True):
        """
        Callback function for leader election.

        Marks the instance as master and locks models in Zookeeper.
        """
        self.im_master = True
        if lock:
            self.locks_models_on_zoo()
        while True:
            time.sleep(self.RB_AIOUTLIERS_MAX_SLEEP)
            self.election_callback(lock=False)