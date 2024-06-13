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
import sys
import signal
from kazoo.client import KazooClient, KazooRetry
from kazoo.protocol.states import KazooState
from resources.src.logger.logger import logger
from resources.src.config.configmanager import ConfigManager

class ZooKeeperClient:
    """
    A client to manage interactions with a ZooKeeper service.

    This class provides methods to set up a ZooKeeper client, handle state changes,
    clean up connections, and manage znodes.
    """

    def __init__(self, config: ConfigManager) -> None:
        """
        Initializes the ZooKeeperClient instance, setting up the ZooKeeper client and
        signal handlers for cleanup.

        Args:
            config (ConfigManager): Configuration settings including the ones for ZooKeeper client.
        """
        self.zookeeper = None
        self._setup_zookeeper(config)
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)

    def _setup_zookeeper(self, config: ConfigManager) -> None:
        """
        Sets up the ZooKeeper client with retry strategies and adds a state listener.

        Args:
            config (ConfigManager): Configuration settings including the ones for ZooKeeper client.
        """
        retry = KazooRetry(
            max_tries=15,
            delay=1.0,
            backoff=2,
            max_delay=30
        )
        self.zookeeper = KazooClient(
            hosts=config.get("ZooKeeper", "zk_hosts").split(","),
            command_retry=retry,
            connection_retry=retry
        )
        self.name = config.get("ZooKeeper", "zk_name")
        self.zookeeper.add_listener(self._listener)
        self.zookeeper.start()

    def _listener(self, state: KazooState) -> None:
        """
        Listens for changes in the ZooKeeper connection state and logs the events.

        Args:
            state (KazooState): The current state of the ZooKeeper connection.
        """
        if state == KazooState.LOST:
            logger.info("SESSION LOST")
        elif state == KazooState.SUSPENDED:
            logger.info("SESSION SUSPENDED")
        elif state == KazooState.CONNECTED:
            logger.info("SESSION CONNECTED")

    def cleanup(self, signum: int, frame) -> None:
        """
        Cleans up the ZooKeeper client and exits the application.

        Args:
            signum (int): The signal number.
            frame: The current stack frame.
        """
        logger.info(f"Cleanup called with signal {signum}")
        self.zookeeper.stop()
        self.zookeeper.close()
        logger.info("Zookeeper connection closed, exiting application")
        sys.exit(0)

    def _check_node(self, *paths: str) -> bool:
        """
        Checks if a znode exists at the specified path.

        Args:
            *paths (str): The parts of the path to join and create the znode.

        Returns:
            bool: Whether or not the znode exists.
        """
        full_path = os.path.join(*paths)
        return self.zookeeper.exists(full_path) is not None

    def _create_node(self, *paths: str, ephemeral: bool = False) -> None:
        """
        Creates a single znode at the specified path.

        Args:
            *paths (str): The parts of the path to join and create the znode.
            ephemeral (bool, optional): Set to true if the node should be ephemeral.
        """
        full_path = os.path.join(*paths)
        self.zookeeper.create(full_path, ephemeral=ephemeral)

    def _delete_node(self, *paths: str) -> None:
        """
        Deletes a single znode at the specified path.

        Args:
            *paths (str): The parts of the path to join and delete the znode.
        """
        full_path = os.path.join(*paths)
        self.zookeeper.delete(full_path)
