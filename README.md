<h3 align=center>tamarind</h3>
<h3 align=center>🥭</h3>
<h6 align=center>manage multiple ephemeral neo4j containers</h6>
<p align=center>
<a href="https://pypi.org/project/tamarind/"><img alt="PyPI" src="https://img.shields.io/pypi/v/tamarind.svg?logo=python&logoColor=orange&style=for-the-badge"></a>
</p>

## Installation

Install from PyPI using pip:

```shell
pip3 install tamarind
```

You will need Docker already installed if you intend to use the Docker provisioning service.


## Usage

### Creating a new db

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

The object returned is a [`py2neo.database.Graph`](https://py2neo.org/v4/database.html#py2neo.database.Graph) object:

```python
>>> N["MyDatabase"].run("MATCH (a:Person) RETURN a.name, a.born LIMIT 4").data()
[{'a.born': 1964, 'a.name': 'Keanu Reeves'},
 {'a.born': 1967, 'a.name': 'Carrie-Anne Moss'},
 {'a.born': 1961, 'a.name': 'Laurence Fishburne'},
 {'a.born': 1960, 'a.name': 'Hugo Weaving'}]


```

### List all

```python
>>> N.ps().keys()
['MyDatabase', 'OldDatabase']
```

### Stop a service

```python
>>> N.stop("OldDatabase")
>>> N.ps().keys()
['MyDatabase']
```

## Legal

Licensed under Apache 2.0. Reach out to opensource@fitmango.com with questions.

> Copyright 2019 FitMango.
>
> Licensed under the Apache License, Version 2.0 (the "License");
> you may not use this codebase except in compliance with the License.
> You may obtain a copy of the License at
>
> http://www.apache.org/licenses/LICENSE-2.0
>
> Unless required by applicable law or agreed to in writing, software
> distributed under the License is distributed on an "AS IS" BASIS,
> WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
> See the License for the specific language governing permissions and
> limitations under the License.

---

<h6 align=center>Made with ❤️ at <a href="https://github.com/fitmango">🥭</a></h6>

