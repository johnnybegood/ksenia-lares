<a id="ksenia_lares.ip_api"></a>

# ksenia\_lares.ip\_api

<a id="ksenia_lares.ip_api.IpAPI"></a>

## IpAPI Objects

```python
class IpAPI(BaseApi)
```

Implementation for the IP range of Kseni Lares (Lare 16 IP, 48 IP & 128 IP).

<a id="ksenia_lares.ip_api.IpAPI.__init__"></a>

#### \_\_init\_\_

```python
def __init__(data: dict) -> None
```

Initialize the API with the necessary connection details.

**Arguments**:

- `data` _dict_ - A dictionary containing the following keys:
  - username (str): The username for authentication.
  - password (str): The password for authentication.
  - host (str): The hostname or IP address of the API.
  - port (int): The port number of the API.
  

**Raises**:

- `ValueError` - If any required parameter is missing or invalid.

<a id="ksenia_lares.ip_api.IpAPI.info"></a>

#### info

```python
async def info() -> AlarmInfo
```

Get info about the alarm system, like name and version

<a id="ksenia_lares.ip_api.IpAPI.get_zones"></a>

#### get\_zones

```python
async def get_zones() -> List[Zone]
```

Get status of all zones

<a id="ksenia_lares.ip_api.IpAPI.get_partitions"></a>

#### get\_partitions

```python
async def get_partitions() -> List[Partition]
```

Get status of partitions

<a id="ksenia_lares.ip_api.IpAPI.get_scenarios"></a>

#### get\_scenarios

```python
async def get_scenarios() -> List[Scenario]
```

Get status of scenarios

<a id="ksenia_lares.ip_api.IpAPI.activate_scenario"></a>

#### activate\_scenario

```python
async def activate_scenario(scenario: int, code: str) -> bool
```

Activate the given scenarios, requires the alarm code

<a id="ksenia_lares.ip_api.IpAPI.bypass_zone"></a>

#### bypass\_zone

```python
async def bypass_zone(zone: int, code: str, bypass: bool) -> bool
```

Activate the given scenarios, requires the alarm code

<a id="ksenia_lares.ip_api.IpAPI.get_model"></a>

#### get\_model

```python
async def get_model() -> str
```

Get model information

