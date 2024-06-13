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

import os
import signal
import time
import threading
import unittest
from unittest.mock import patch, MagicMock
from resources.src.config.configmanager import ConfigManager
from resources.src.redborder.zookeeper.zookeeper_client import ZooKeeperClient
from resources.src.redborder.zookeeper.rb_outliers_zoo_sync import RbOutliersZooSync
from kazoo.recipe.election import Election
from kazoo.recipe.queue import LockingQueue
from kazoo.recipe.watchers import ChildrenWatch
from kazoo.exceptions import LockTimeout
from resources.src.redborder.s3 import S3
from resources.src.logger.logger import logger

config_path = "resources/tests/config_test.ini"
config = ConfigManager(config_path)
tick_time = float(config.get("ZooKeeper", "zk_tick_time"))
sleep_time = float(config.get("ZooKeeper", "zk_sleep_time"))
class SyncThreadContext:
    def __init__(self, target, zk_sync):
        self.target = target
        self.zk_sync = zk_sync
        self.thread = threading.Thread(target=self.target)

    def __enter__(self):
        self.zk_sync.is_running = True
        self.thread.start()
        time.sleep(sleep_time)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.zk_sync.is_running = False
        self.thread.join()

class TestRbOutliersZooSync(unittest.TestCase):

    def setUp(self):
        self.zk_sync = RbOutliersZooSync(config)
        try:
            self.zk_sync.s3_client.s3_client.create_bucket(Bucket=self.zk_sync.s3_client.bucket_name)
        except:
            pass
        self.sync_thread = SyncThreadContext(self.zk_sync.sync_nodes, self.zk_sync)

    def tearDown(self):
        self.zk_sync.is_running = False
        self.zk_sync.is_leader = False
        time.sleep(sleep_time)
        try:
            self.zk_sync.s3_client.s3_client.delete_bucket(Bucket=self.zk_sync.s3_client.bucket_name)
        except:
            print("Coulden't delete bucket")
        try:
            self.zk_sync.zookeeper.delete(config.get("ZooKeeper", "zk_sync_path"), recursive=True)
        except:
            print("Couldn't delete zookeeper")
        return super().tearDown()

    def test_ensure_paths(self):
        self.zk_sync._ensure_paths()
        zk_sync_path = config.get("ZooKeeper", "zk_sync_path")
        expected_paths = [
            os.path.join(zk_sync_path, "leader"),
            os.path.join(zk_sync_path, "models", "queue"),
            os.path.join(zk_sync_path, "models", "taken"),
            os.path.join(zk_sync_path, "models", "train"),
            os.path.join(zk_sync_path, "election")
        ]
        for path in expected_paths:
            self.assertTrue(self.zk_sync._check_node(path))

    def test_setup_s3(self):
        self.assertIsInstance(self.zk_sync.s3_client, S3)

    def test_sync_nodes(self):
        with self.sync_thread:
            self.assertTrue(self.zk_sync.is_running)
            self.assertIsInstance(self.zk_sync.queue, LockingQueue)
            self.assertIsInstance(self.zk_sync.election, Election)
            self.assertIsInstance(self.zk_sync.leader_watcher, ChildrenWatch)

    def test_cleanup(self):
        mock_cleanup = MagicMock()
        with patch.object(ZooKeeperClient, 'cleanup', mock_cleanup):
            with self.sync_thread:
                self.zk_sync.cleanup(signal.SIGINT, None)
                self.assertFalse(self.zk_sync.is_running)
                self.assertFalse(self.zk_sync.is_leader)
                mock_cleanup.assert_called_once_with(signal.SIGINT, None)


    @patch('resources.src.redborder.zookeeper.rb_outliers_zoo_sync.RbOutlierTrainJob')
    def test_leader_tasks(self, mock_train_job):
        with self.sync_thread:
            self.zk_sync.is_leader = True
            mock_models = ['model1', 'model2']
            self.zk_sync._get_models = MagicMock(return_value=mock_models)
            self.zk_sync._create_node(self.zk_sync.paths["taken"], "model1")

            time.sleep(sleep_time)
            queue=self.zk_sync.zookeeper.get_children(self.zk_sync.paths["queue"]+"/entries")
            self.assertTrue(len(queue)==3) #Several loops of queueing + one requeued node
            self.assertFalse(self.zk_sync._check_node(self.zk_sync.paths["taken"], "model3"))

    def test_follower_tasks(self):
        self.zk_sync.outlier_job = MagicMock()
        with self.sync_thread:
            self.zk_sync.is_leader = False
            self.zk_sync.queue.put(b"model1")
            queue_len = len(self.zk_sync.zookeeper.get_children(self.zk_sync.paths["queue"]+"/entries"))
            self.assertTrue(queue_len==1)
            time.sleep(sleep_time)
            queue_len = len(self.zk_sync.zookeeper.get_children(self.zk_sync.paths["queue"]+"/entries"))
            self.assertTrue(queue_len==0)
            self.assertFalse(self.zk_sync._check_node(self.zk_sync.paths["taken"], "model1"))
            self.assertFalse(self.zk_sync._check_node(self.zk_sync.paths["train"], "model1"))

    def test_participate_in_election(self):
        with self.sync_thread:
            self.zk_sync._leader_exists = MagicMock(return_value=False)
            self.zk_sync._get_leader_name = MagicMock(return_value='leader_name')
            self.zk_sync.election.lock = MagicMock()
            self.zk_sync.election.lock.acquire = MagicMock(return_value=True)
            self.zk_sync.election.lock.release = MagicMock()
            self.zk_sync._participate_in_election([])
            self.zk_sync.election.lock.acquire.assert_called_once()
            self.zk_sync.election.lock.release.assert_called_once()
            self.assertEqual(self.zk_sync.is_leader, self.zk_sync.name == 'leader_name')

    def test_get_models(self):
        self.zk_sync.s3_client.list_objects_in_folder = MagicMock(
            return_value=['rbaioutliers/latest/model1.ini', 'rbaioutliers/latest/model2.ini']
        )
        models = self.zk_sync._get_models()
        self.assertEqual(models, ['model1', 'model2'])

    def test_get_model_from_queue(self):
        with self.sync_thread:
            self.zk_sync.queue.put(b"model1")
            model = self.zk_sync._get_model_from_queue()
            self.assertEqual(model, 'model1')
            self.assertTrue(self.zk_sync._check_node(self.zk_sync.paths["train"], "model1"))
            self.assertTrue(self.zk_sync._check_node(self.zk_sync.paths["taken"], "model1"))


    def test_process_model_as_follower(self):
        self.zk_sync.outlier_job = MagicMock()
        with self.sync_thread:
            self.zk_sync._create_node(self.zk_sync.paths["train"], "model1")
            self.zk_sync._create_node(self.zk_sync.paths["taken"], "model1")
            self.zk_sync._process_model_as_follower('model1')
            self.assertFalse(self.zk_sync._check_node(self.zk_sync.paths["train"], "model1"))
            self.assertFalse(self.zk_sync._check_node(self.zk_sync.paths["taken"], "model1"))

if __name__ == "__main__":
    unittest.main()
