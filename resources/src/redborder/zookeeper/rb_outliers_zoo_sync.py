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
import time
from kazoo.recipe.election import Election
from kazoo.recipe.queue import LockingQueue
from kazoo.recipe.watchers import ChildrenWatch
from kazoo.exceptions import LockTimeout
from resources.src.redborder.s3 import S3
from resources.src.logger.logger import logger
from resources.src.config.configmanager import ConfigManager
from resources.src.redborder.async_jobs.train_job import RbOutlierTrainJob
from resources.src.redborder.zookeeper.zookeeper_client import ZooKeeperClient

class RbOutliersZooSync(ZooKeeperClient):
    """
    A client for synchronizing and managing leader election in a ZooKeeper-based environment,
    specifically for handling outlier models.

    This class extends `ZooKeeperClient` to include functionality for leader election,
    synchronization, and model processing tasks.
    """

    def __init__(self, config: ConfigManager) -> None:
        """
        Initializes the RbOutliersZooSync instance, setting up the necessary attributes and
        configurations, including the ZooKeeper client and S3 client.

        Args:
            config (ConfigManager): Configuration settings including the ones for the ZooKeeper
                and S3 clients.
        """
        self.is_leader = False
        self.is_running = False
        self.queue = None
        self.election = None
        self.leader_watcher = None
        self.paths = {}
        super().__init__(config)
        self.sleep_time = float(config.get("ZooKeeper", "zk_sleep_time"))
        self.tick_time = float(config.get("ZooKeeper", "zk_tick_time"))
        self.zk_sync_path = config.get("ZooKeeper", "zk_sync_path")
        self.setup_s3(config)
        self.outlier_job = RbOutlierTrainJob(config)

    def _tick(self) -> None:
        time.sleep(self.tick_time)

    def _ensure_paths(self) -> None:
        """
        Ensures the required ZooKeeper paths are created.
        """
        self.paths = {
            "leader": os.path.join(self.zk_sync_path, "leader"),
            "queue": os.path.join(self.zk_sync_path, "models", "queue"),
            "taken": os.path.join(self.zk_sync_path, "models", "taken"),
            "train": os.path.join(self.zk_sync_path, "models", "train"),
            "election": os.path.join(self.zk_sync_path, "election")
        }
        for path in self.paths.values():
            self.zookeeper.ensure_path(path)

    def setup_s3(self, config) -> None:
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
        self._ensure_paths()
        self.is_running = True
        self.queue = LockingQueue(self.zookeeper, self.paths["queue"])
        self.election = Election(self.zookeeper, self.paths["election"], identifier=self.name)
        self.leader_watcher = ChildrenWatch(
            self.zookeeper,
            self.paths["leader"],
            self._participate_in_election
        )
        self._run_tasks()

    def cleanup(self, signum: int, frame) -> None:
        """
        Cleans up the resources and stops the synchronization process.

        Args:
            signum (int): The signal number.
            frame: The current stack frame.
        """
        logger.info(f"Cleanup called with signal {signum}")
        self.is_running = False
        self.election.cancel()
        if self.leader_watcher is not None:
            self.leader_watcher._stopped = True
        if self.is_leader:
            self.is_leader = False
            self.zookeeper.set(self.paths["leader"], b"")
        self._tick()
        self._tick()
        super().cleanup(signum, frame)

    def _run_tasks(self) -> None:
        """
        Runs tasks based on the leadership status.
        """
        while self.is_running:
            if self.is_leader:
                self._leader_tasks()
            else:
                self._follower_tasks()
            self._tick()

    def _leader_tasks(self) -> None:
        """
        Runs the tasks for the leader node. This involves queuing models to be trained by the
        followers and requeuing models whose clients or training have failed.
        """
        logger.info("Running leader tasks")
        while self.is_leader and self.is_running:
            models = self._get_models()
            self._queue_models_on_zoo(models)
            next_task_time = time.time() + self.sleep_time
            while time.time() < next_task_time and self.is_running:
                for model in models:
                    is_taken = self._check_node(self.paths["taken"], model)
                    is_training = self._check_node(self.paths["train"], model)
                    if is_taken and not is_training:
                        logger.error(f"Failure processing model {model}")
                        self._delete_node(self.paths["taken"], model)
                        self.queue.put(bytes(model, "utf-8"))
                        logger.info(f"Model {model} requeued")
                self._tick()

    def _follower_tasks(self) -> None:
        """
        Runs the tasks for the follower nodes.
        """
        logger.info("Running follower tasks")
        while self.is_running and not self.is_leader:
            if not self._leader_exists():
                logger.info("No leader found, waiting...")
                self._tick()
                continue
            model = self._get_model_from_queue()
            if model:
                self._process_model_as_follower(model)
            self._tick()

    def _participate_in_election(self, leader_nodes: list[str]) -> None:
        """
        Participates in the leader election process.

        Args:
            leader_nodes (list[str]): A list of leader nodes.
        """
        if not self._leader_exists() and self.is_running:
            logger.info(f"Participating in election {len(leader_nodes)} nodes")
            try:
                if self.election.lock.acquire(timeout=5*self.tick_time):
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

    def _get_models(self) -> list[str]:
        """
        Retrieves the models from S3.

        Returns:
            list[str]: Names of the models to train.
        """
        prefix = "rbaioutliers/latest/"
        models = self.s3_client.list_objects_in_folder(prefix)
        models = [model[len(prefix):] if model.startswith(prefix) else model for model in models]
        return [model.replace('.ini', '') for model in models if '.ini' in model]

    def _queue_models_on_zoo(self, models: list[str]) -> None:
        """
        Queues the models in ZooKeeper.

        Args:
            models (list[str]): A list of models to be locked.
        """
        if self.is_leader and self.is_running:
            b_models = [bytes(model, "utf-8") for model in models]
            self.queue.put_all(b_models)
            logger.info(f"Queued models {', '.join(models)}")

    def _get_model_from_queue(self) -> str:
        """
        Attempts to get a model from the queue. Then, znodes with the model name are created both
        in the train and in the taken nodes to indicate that the model is being trained. This is
        made so if the follower fails, the ephemeral node in "train" will disappear while the node
        in "taken" would remain. The leader will notice this abnormal state and requeue the model.

        Returns:
            str: The model as a string if successful, otherwise None.
        """
        try:
            model = self.queue.get(timeout=2).decode("utf-8")
            self._create_node(self.paths["train"], model, ephemeral=True)
            self.queue.consume()
            self._create_node(self.paths["taken"], model, ephemeral=False)
            logger.info(f"Follower {self.name} locked model {model}")
            return model
        except AttributeError:
            logger.info("Queue is empty. Waiting for items...")
            return None

    def _process_model_as_follower(self, model: str) -> None:
        """
        Processes the model as a follower node.

        Args:
            model (str): The model to process.
        """
        try:
            self.outlier_job.train_job(model)
            self._delete_node(self.paths["taken"], model)
            self._delete_node(self.paths["train"], model)
            logger.info(f"Finished training of model {model}")
        except Exception as e:
            logger.error(f"Client {self.name} failed to process {model}: {e}")
            self._delete_node(self.paths["taken"], model)
