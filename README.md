<h3 align=center>tamarind</h3>
<h3 align=center>🥭</h3>
<h6 align=center>manage multiple ephemeral neo4j containers</h6>



## Usage

```python
from tamarind import Neo4jDockerProvisioner

N = Neo4jDockerProvisioner()

N.start("MyDatabase")
```

Now you can access this graph database through py2neo:

```python
>>> N["MyDatabase"]
<py2neo.Graph>
```

List all with:

```python
>>> N.ps().keys()
['MyDatabase', 'OldDatabase']
```
