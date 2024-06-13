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

import unittest
import signal
import os
from unittest.mock import patch
from kazoo.client import KazooClient, KazooRetry
from kazoo.protocol.states import KazooState
from resources.src.config.configmanager import ConfigManager
from resources.src.logger.logger import logger
from resources.src.redborder.zookeeper.zookeeper_client import ZooKeeperClient  # Replace with the actual import

class TestZooKeeperClient(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create a real instance of ConfigManager with a test configuration file
        cls.config = ConfigManager("resources/tests/config_test.ini")
        cls.zk_client = ZooKeeperClient(cls.config)

    @classmethod
    def tearDownClass(cls):
        # Ensure ZooKeeper client is properly cleaned up after all tests
        cls.zk_client.zookeeper.stop()

    @patch('sys.exit')
    def test_cleanup(self, mock_exit):
        self.zk_client.zookeeper.start()
        self.zk_client.cleanup(signal.SIGINT, None)
        self.assertFalse(self.zk_client.zookeeper.connected)
        mock_exit.assert_called_once_with(0)

    def test_setup_zookeeper(self):
        self.assertIsInstance(self.zk_client.zookeeper, KazooClient)

    def test_check_node(self):
        self.zk_client.zookeeper.start()
        # Test checking the existence of a node in ZooKeeper
        self.zk_client.zookeeper.ensure_path("/test/node")
        result = self.zk_client._check_node('/test', 'node')
        self.assertTrue(result)
        self.zk_client.zookeeper.delete("/test/node")

    def test_create_node(self):
        self.zk_client.zookeeper.start()
        # Test creating a node in ZooKeeper
        self.zk_client._create_node('/test', 'node', ephemeral=False)
        self.assertTrue(self.zk_client.zookeeper.exists("/test/node"))
        self.zk_client.zookeeper.delete("/test/node")

    def test_delete_node(self):
        self.zk_client.zookeeper.start()
        # Test deleting a node in ZooKeeper
        self.zk_client.zookeeper.ensure_path("/test/node")
        self.zk_client._delete_node('/test', 'node')
        self.assertIsNone(self.zk_client.zookeeper.exists("/test/node"))

if __name__ == '__main__':
    unittest.main()
