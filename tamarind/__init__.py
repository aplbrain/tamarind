"""
Copyright 2019-2021 FitMango.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this codebase except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Tamarind base implementation Jan 17 2018
"""
import abc
from typing import Dict, List, Tuple
import time
import os

import docker
import py2neo

_DEFAULT_SLEEP_INCREMENT = 3.0


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


_DEFAULT_PASSWORD = "neo4jpw"


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
            password (str): A password to set to protect the database. Default
                is tamarind._DEFAULT_PASSWORD. You shouldn't rely on this for
                security, duh!

        Returns:
            None

        """
        self._autoremove_containers = kwargs.get("autoremove_containers", True)
        self._initial_heap_size = kwargs.get("initial_heap_size", "2G")
        self._max_memory_size = kwargs.get("max_memory_size", "4G")
        self._password = kwargs.get("password", _DEFAULT_PASSWORD)
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
        return max([7686, *self.ports.values()]) + 1

    def start(
        self,
        name: str,
        wait: bool = True,
        data_path: str = None,
        import_path: str = None,
        use_data_path: bool = True,
        use_import_path: bool = False,
        mount_browser: bool = False,
        run_before: str = "",
        run_after: str = "",
        image_name: str = "neo4j:4.2",
        wait_attempt_limit: int = 20,
    ) -> Tuple[str, int]:
        """
        Start a new database.

        Arguments:
            name (str): The name of the new instance. Any string, no spaces.
            wait (bool): Whether to wait upon working graph before returning.
                Defaults to True.
            data_path (str): The path to data. Only used if use_data_path is
                set to True.
            import_path (str): The path to point to in order to run an import.
                Only used if use_import_path is set to True.
            use_data_path (bool: True): If /data should be mounted.
            use_import_path (bool: False): If /import should be mounted. Note
                that unlike use_data_path, this defaults to False!
            mount_browser (bool: False): Whether to mount the browser-friendly
                port 7474. Note that this only works on ONE container at a time
                because Tamarind does not yet support multiport HTTP.
            run_before (str): A bash command to run prior to starting the db.
            run_before (str): A bash command to run prior to starting the db.
            image_name (str: "neo4j:4.2"): An image to run, if different from
                the default Neo4j database image.
            wait_attempt_limit (int: 20): How many times to check the container
                for signs of life before throwing an error. These are separated
                by 3 seconds, so the default timeout is 1 minute.

        Returns:
            (str, int): The port on which this container is listening (bolt://)

        """
        if name in self.ps():
            raise ValueError(f"Cannot start {name}, already running!")

        volumes = {}

        if use_data_path or data_path:
            if data_path is None:
                data_path = f"{os.getcwd()}/data/{name}"
            volumes[data_path] = {"bind": "/data", "mode": "rw"}
        if use_import_path or import_path:
            if import_path is None:
                import_path = f"{os.getcwd()}/import/{name}"
            volumes[import_path] = {"bind": "/import", "mode": "ro"}

        port = self._next_port()

        internal_port = 7687

        ports = {internal_port: port}
        if mount_browser:
            ports[7474] = 7474
            ports[7473] = 7473

        if run_before:
            run_before += " ;"

        if run_after:
            run_after = " && " + run_after

        _running_container = self.docker.containers.run(
            image_name,
            name=f"tamarind_{name}",
            command=f"""bash -c '{run_before} ./bin/neo4j-admin set-initial-password {self._password} && neo4j start {run_after} && tail -f /dev/null'""",
            auto_remove=self._autoremove_containers,
            detach=True,
            environment={
                "NEO4J_dbms_memory_heap_initial__size": self._initial_heap_size,
                "NEO4J_dbms_memory_heap_max__size": self._max_memory_size,
                "NEO4J_dbms_connector_bolt_listen__address": f"0.0.0.0:{internal_port}",
                "NEO4J_dbms_connector_bolt_advertised__address": f"0.0.0.0:{internal_port}",
            },
            volumes=volumes,
            ports=ports,
        )

        if wait:
            attempts = 0
            # Loop until you get bored or hit a timeout:
            tic = time.time()
            while attempts < wait_attempt_limit:
                attempts += 1
                time.sleep(_DEFAULT_SLEEP_INCREMENT)
                try:
                    _running_container.reload()
                except:
                    raise OSError(f"Container {name} has died.")
                try:
                    self[name].run("MATCH (a) RETURN a LIMIT 1")
                    break
                except:
                    pass
            else:
                elapsed = time.time() - tic
                raise ValueError(
                    f"Timeout encountered after {elapsed}s. If you are importing a very large graph, consider increasing your `wait` argument to `Tamarind#start()`."
                )

        return (_running_container, port)

    def stop(self, key: str) -> None:
        """
        Stop a container with a given key.

        Arguments:
            key (str): The key of the container to kill

        Returns:
            None

        """
        self.docker.containers.get(f"tamarind_{key}").stop()
        if not self._autoremove_containers:
            # If autoremove is True, then this is redundant and will fail.
            self.docker.containers.get(f"tamarind_{key}").remove()

    def ps(self) -> Dict[str, int]:
        """
        List all currently running tamarind services.

        Wraps docker ps.
        """
        return {
            c.name.split("tamarind_")[1]: (
                int(
                    list(
                        filter(
                            lambda x: x,
                            self.docker.api.inspect_container(c.id)["NetworkSettings"][
                                "Ports"
                            ].values(),
                        )
                    )[0][0]["HostPort"]
                )
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
        cport = self.ps()[f"{key}"]
        return py2neo.Graph(
            f"bolt://localhost:{cport}", username="neo4j", password=self._password
        )
