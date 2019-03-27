"""
Tamarind base implementation Jan 17 2018
"""
import abc
from typing import Dict, List

import os

import docker
import py2neo


class Neo4jProvisioner(abc.ABC):
    """
    Abstract base class for Neo4j database provisioner.

    .
    """

    def start(self, name: str, wait: bool = False) -> int:
        """
        Start a new database.

        Arguments:
            name (str): The name of the new instance. Any string, no spaces.
            wait (bool): Whether to wait upon working graph before returning.
                Defaults to False, and currently does not work.

        Returns:
            int

        """
        return NotImplemented

    def ps(self) -> Dict[str, int]:
        """
        Get a list of all running databases.

        Arguments:
            None
        """
        return NotImplemented

    def __getitem__(self, key: str) -> py2neo.Graph:
        return NotImplemented


class Neo4jDockerProvisioner:
    """
    A database provisioning service that creates docker containers locally.

    This is good for quick prototyping, esp. when you are in a directory
    to which you anticipate mounting and running serveral non-persistant dbs.
    """

    def __init__(self, **kwargs):
        """
        Create a new Neo4jDockerProvisioner.

        Arguments:
            autoremove_containers (bool: True): Whether to autoremove when done
            initial_heap_size (str): 2G
            max_memory_size (str): 4G

        Returns:
            None

        """
        self._autoremove_containers = kwargs.get("autoremove_containers", True)
        self._initial_heap_size = kwargs.get("initial_heap_size", "2G")
        self._max_memory_size = kwargs.get("max_memory_size", "4G")
        self.docker = docker.from_env()
        self.ports: Dict[str, int] = self.ps()

    def _next_port(self) -> int:
        """
        Get the next port (in order) starting with 7687.

        Arguments:
            None

        Returns:
            int

        """
        return max([7687, *self.ports.values()]) + 1

    def start(self, name: str, wait: bool = False) -> int:
        """
        Start a new database.

        Arguments:
            name (str): The name of the new instance. Any string, no spaces.
            wait (bool): Whether to wait upon working graph before returning.
                Defaults to False, and currently does not work.

        Returns:
            int: The port on which this container is listening (bolt://)

        """
        if name in self.ps():
            raise ValueError(f"Cannot start {name}, already running!")

        port = self._next_port()
        _running_container = self.docker.containers.run(
            "neo4j:3.4",
            name=f"tamarind_{name}",
            command="""
            bash -c './bin/neo4j-admin set-initial-password neo4jpw && ./bin/neo4j start && tail -f /dev/null'""",
            auto_remove=self._autoremove_containers,
            detach=True,
            environment={
                "NEO4J_dbms_memory_heap_initial__size": self._initial_heap_size,
                "NEO4J_dbms_memory_heap_max__size": self._max_memory_size,
                "NEO4J_dbms_connector_bolt_listen__address": f":{port}",
                "NEO4J_dbms_connector_bolt_advertised__address": f":{port}",
            },
            volumes={f"{os.getcwd()}/data/{name}": {"bind": "/data", "mode": "rw"}},
            ports={port: port},
            network_mode="bridge",
        )
        return port

    def stop(self, key: str) -> None:
        self.docker.containers.get(f"tamarind_{key}").stop()
        self.docker.containers.get(f"tamarind_{key}").remove()

    def ps(self) -> Dict[str, int]:
        """
        List all currently running tamarind services.

        Wraps docker ps.
        """
        return {
            c.name: (
                self.docker.api.inspect_container(c.id)["NetworkSettings"]["Ports"]
            )
            for c in self.docker.containers.list()
            if "tamarind_" in c.name
        }

    def __getitem__(self, key: str) -> py2neo.Graph:
        """
        Get access directly to a running tamarind neo4j instance.

        Arguments:
            key (str): The name of the db (same as what you passed to the
            Neo4jDockerProvisioner#start(KEY) call).

        Returns:
            py2neo.Graph: A pointer to the database

        """
        cport = self.ps()[f"tamarind_{key}"]
        cport = cport[max(cport.keys())][0]["HostPort"]
        return py2neo.Graph(
            f"bolt://localhost:{cport}", username="neo4j", password="neo4jpw"
        )
