"""
Tamarind base implementation Jan 17 2018
"""
import abc
from typing import Dict, List

import os

import docker
import py2neo

class Neo4jProvisioner(abc.ABC):

    def start(self, name: str, wait: bool = False) -> int:
        ...

    def ps(self) -> Dict[str, int]:
        ...

    def __getitem__(self, key: str) -> py2neo.Graph:
        ...



class Neo4jDockerProvisioner:

    def __init__(self, **kwargs):

        self._autoremove_containers = kwargs.get("autoremove_containers", True)
        self._initial_heap_size = kwargs.get("initial_heap_size", "2G")
        self._max_memory_size = kwargs.get("max_memory_size", "4G")
        self.docker = docker.from_env()
        self.ports: Dict[str, int] = self.ps()

    def _next_port(self):
        return max([7687, *self.ports.values()]) + 1

    def start(self, name: str, wait: bool = False) -> int:
        if name in self.ps():
            raise ValueError(f"Cannot start {name}, already running!")

        port = self._next_port()
        _running_container = self.docker.containers.run(
            "neo4j:3.4",
            name=f"tamarind_{name}",
            command="""
            bash -c './bin/neo4j-admin set-initial-password neo4jpw && ./bin/neo4j start && tail -f /dev/null'""",
            # auto_remove=self._autoremove_containers,
            detach=True,
            environment={
                "NEO4J_dbms_memory_heap_initial__size": self._initial_heap_size,
                "NEO4J_dbms_memory_heap_max__size": self._max_memory_size,
                "NEO4J_dbms_connector_bolt_listen__address": f":{port}",
                "NEO4J_dbms_connector_bolt_advertised__address": f":{port}",
                # "NEO4J_dbms_security_procedures_unrestricted": "apoc.\\\*",
            },
            volumes={
                # f"{os.getcwd()}/data/{name}": {"bind": "/data", "mode": "rw"}
            },
            ports={
                # 7474: port,
                port: port,
            },
            network_mode="bridge",
        )
        return port


    def ps(self) -> Dict[str, int]:
        return {
            c.name: (
                self.docker.api.inspect_container(c.id)['NetworkSettings']['Ports']
            )
            for c in self.docker.containers.list()
            if "tamarind_" in c.name
        }


    def __getitem__(self, key: str) -> py2neo.Graph:
        cport = self.ps()[f"tamarind_{key}"]
        cport = cport[max(cport.keys())][0]['HostPort']
        return py2neo.Graph(f"bolt://localhost:{cport}", username="neo4j", password="neo4jpw")
