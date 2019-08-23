## *Class* `Neo4jProvisioner(abc.ABC)`


Abstract base class for Neo4j database provisioner.

.


## *Function* `start(self, name: str, wait: bool = False) -> int`


Start a new database.

### Arguments
> - **name** (`str`: `None`): The name of the new instance. Any string, no spaces.     wait (bool): Whether to wait upon working graph before returning.
        Defaults to False, and currently does not work.

### Returns
    int



## *Function* `ps(self) -> Dict[str, int]`


Get a list of all running databases.

### Arguments
    None


## *Class* `Neo4jDockerProvisioner`


A database provisioning service that creates docker containers locally.

This is good for quick prototyping, esp. when you are in a directory to which you anticipate mounting and running serveral non-persistant dbs.


## *Function* `__init__(self, **kwargs)`


Create a new Neo4jDockerProvisioner.

### Arguments
> - **autoremove_containers** (`bool`: `True`): Whether to autoremove when done     initial_heap_size (str): 2G     max_memory_size (str): 4G

### Returns
    None



## *Function* `_next_port(self) -> int`


Get the next port (in order) starting with 7687.

### Arguments
    None

### Returns
    int



## *Function* `ps(self) -> Dict[str, int]`


List all currently running tamarind services.

Wraps docker ps.


## *Function* `__getitem__(self, key: str) -> py2neo.Graph`


Get access directly to a running tamarind neo4j instance.

### Arguments
> - **key** (`str`: `None`): The name of the db (same as what you passed to the     Neo4jDockerProvisioner#start(KEY) call).

### Returns
> - **py2neo.Graph** (`None`: `None`): A pointer to the database


