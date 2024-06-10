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

import os
import random
import time
from kazoo.recipe.election import Election
from kazoo.recipe.queue import LockingQueue
from kazoo.recipe.watchers import ChildrenWatch
from kazoo.exceptions import LockTimeout
from resources.src.redborder.s3 import S3
from resources.src.server.rest import config
from resources.src.logger.logger import logger
from resources.src.redborder.async_jobs.train_job import RbOutlierTrainJob
from resources.src.redborder.zookeeper.zookeeper_client import ZooKeeperClient

class RbOutliersZooSync(ZooKeeperClient):
    """
    A client for synchronizing and managing leader election in a ZooKeeper-based environment,
    specifically for handling outlier models.

    This class extends `ZooKeeperClient` to include functionality for leader election,
    synchronization, and model processing tasks.
    """

    def __init__(self) -> None:
        """
        Initializes the RbOutliersZooSync instance, setting up the necessary attributes and
        configurations, including the ZooKeeper client and S3 client.
        """
        self.is_leader = False
        self.running = False
        self.s3_client = None
        self.queue = None
        self.election = None
        self.models=[]
        self.paths = {}
        super().__init__()
        self.sleep_time = float(config.get("ZooKeeper", "zk_sleep_time"))
        self.s3_client = None

    def _ensure_paths(self) -> None:
        """
        Ensures the required ZooKeeper paths are created.
        """
        zk_sync_path = config.get("ZooKeeper", "zk_sync_path")
        self.paths = {
            "leader": os.path.join(zk_sync_path, "leader"),
            "queue": os.path.join(zk_sync_path, "models", "queue"),
            "taken": os.path.join(zk_sync_path, "models", "taken"),
            "train": os.path.join(zk_sync_path, "models", "train"),
            "election": os.path.join(zk_sync_path, "election")
        }
        for path in self.paths.values():
            self.zookeeper.ensure_path(path)

    def setup_s3(self) -> None:
        """
        Sets up the S3 client with the necessary configurations.
        """
        self.s3_client = S3(
            config.get("AWS", "s3_public_key"),
            config.get("AWS", "s3_private_key"),
            config.get("AWS", "s3_region"),
            config.get("AWS", "s3_bucket"),
            config.get("AWS", "s3_hostname")
        )

    def sync_nodes(self) -> None:
        """
        Synchronizes the nodes and starts the election and task processes.
        """
        logger.info("Synchronizing nodes")
        self.setup_s3()
        self._ensure_paths()
        self.running = True
        self.queue = LockingQueue(self.zookeeper, self.paths["queue"])
        self.election = Election(self.zookeeper, self.paths["election"], identifier=self.name)
        self.leader_watcher = ChildrenWatch(self.zookeeper, self.paths["leader"], self._participate_in_election)
        self._run_tasks()

    def cleanup(self, signum: int, frame) -> None:
        """
        Cleans up the resources and stops the synchronization process.

        Parameters:
            signum (int): The signal number.
            frame: The current stack frame.
        """
        logger.info(f"Cleanup called with signal {signum}")
        self.running = False
        self.election.cancel()
        self.leader_watcher._stopped = True
        if self.is_leader:
            self.is_leader = False
            self.zookeeper.set(self.paths["leader"], b"")
        time.sleep(2)
        super().cleanup(signum, frame)

    def _run_tasks(self) -> None:
        """
        Runs tasks based on the leadership status.
        """
        while self.running:
            if self.is_leader:
                self._leader_tasks()
            else:
                self._follower_tasks()
            time.sleep(2)

    def _leader_tasks(self) -> None:
        """
        Runs the tasks for the leader node.
        """
        logger.info("Running leader tasks")
        while self.is_leader and self.running:
            self._get_models()
            self._locks_models_on_zoo()
            next_task_time = time.time() + self.sleep_time
            while time.time() < next_task_time:
                for model in self.models:
                    is_taken = self._check_node(self.paths["taken"], model)
                    is_training = self._check_node(self.paths["train"], model)
                    if is_taken and not is_training:
                        logger.error(f"Failure processing model {model}")
                        self._delete_node(self.paths["taken"], model)
                        self.queue.put(bytes(model, "utf-8"))
                        logger.info(f"Model {model} requeued")
                time.sleep(2)

    def _follower_tasks(self) -> None:
        """
        Runs the tasks for the follower nodes.
        """
        logger.info("Running follower tasks")
        while self.running:
            while not self.is_leader and self._leader_exists():
                model = self._get_model_from_queue()
                if model:
                    self._process_model_as_follower(model)
                time.sleep(2)
            time.sleep(2)

    def _participate_in_election(self, leader_nodes: list[str]) -> None:
        """
        Participates in the leader election process.

        Parameters:
            leader_nodes (list[str]): A list of leader nodes.
        """
        if not self._leader_exists() and self.running:
            logger.info("Participating in election")
            try:
                if self.election.lock.acquire(timeout=10):
                    try:
                        self._election_callback()
                    finally:
                        self.election.lock.release()
            except LockTimeout:
                logger.info("Lost election")
        leader = self._get_leader_name()
        self.is_leader = leader == self.name
        logger.info(f"The leader is {leader}")

    def _election_callback(self) -> None:
        """
        Callback function for election events.
        """
        try:
            self._create_node(self.paths["leader"], self.name, ephemeral=True)
            self.zookeeper.set(self.paths["leader"], bytes(self.name, "utf-8"))
        except Exception as e:
            logger.error(f"Failed to create leader node: {e}")

    def _get_leader_name(self) -> str:
        """
        Retrieves the name of the current leader.

        Returns:
            str: The name of the leader.
        """
        try:
            data, _ = self.zookeeper.get(self.paths["leader"])
            return data.decode("utf-8")
        except Exception as e:
            logger.error(f"Error getting leader name: {e}")
            return None

    def _leader_exists(self) -> bool:
        """
        Checks if a leader node exists.

        Returns:
            bool: True if a leader node exists, False otherwise.
        """
        return len(self.zookeeper.get_children(self.paths["leader"])) == 1

    def _get_models(self) -> None:
        """
        Retrieves the models from S3.
        """
        models = self.s3_client.list_objects_in_folder("rbaioutliers/latest")
        self.models = [model.replace('.ini', '') for model in models if '.ini' in model]

    def _locks_models_on_zoo(self) -> None:
        """
        Locks the models in ZooKeeper.
        """
        if self.is_leader and self.running:
            b_models = [bytes(model, "utf-8") for model in self.models]
            self.queue.put_all(b_models)
            logger.info(f"Locked models {', '.join(self.models)}")

    def _get_model_from_queue(self) -> str:
        """
        Attempts to get a model from the queue.

        Returns:
            str: The model as a string if successful, otherwise None.
        """
        try:
            model = self.queue.get(timeout=2).decode("utf-8")
            self.queue.consume()
            self._create_node(self.paths["train"], model, ephemeral=True)
            self._create_node(self.paths["taken"], model, ephemeral=False)
            logger.info(f"Follower {self.name} locked model {model}")
            return model
        except AttributeError:
            logger.info("Queue is empty. Waiting for items...")
            return None

    def _process_model_as_follower(self, model: str) -> None:
        """
        Processes the model as a follower node.

        Parameters:
            model (str): The model to process.
        """
        try:
            outlier_job = RbOutlierTrainJob()
            outlier_job.train_job(model)
            self._delete_node(self.paths["taken"], model)
            self._delete_node(self.paths["train"], model)
            logger.info(f"Finished training of model {model}")
        except Exception as e:
            logger.error(f"Client {self.name} failed to process {model}: {e}")
            self.queue.put(bytes(model, "utf-8"))
            logger.error(f"Client {self.name} requeued {model}")
