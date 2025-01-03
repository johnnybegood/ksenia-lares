<a id="ksenia_lares.base_api"></a>

# ksenia\_lares.base\_api

<a id="ksenia_lares.base_api.BaseApi"></a>

## BaseApi Objects

```python
class BaseApi(ABC)
```

<a id="ksenia_lares.base_api.BaseApi.info"></a>

#### info

```python
@abstractmethod
async def info() -> AlarmInfo
```

Get info about the alarm system, like name and version

<a id="ksenia_lares.base_api.BaseApi.get_zones"></a>

#### get\_zones

```python
@abstractmethod
async def get_zones() -> List[Zone]
```

Get status of alarm zones

<a id="ksenia_lares.base_api.BaseApi.activate_scenario"></a>

#### activate\_scenario

```python
@abstractmethod
async def activate_scenario(scenario: int, code: str) -> bool
```

Activate the given scenarios, requires the alarm code

<a id="ksenia_lares.base_api.BaseApi.get_partitions"></a>

#### get\_partitions

```python
@abstractmethod
async def get_partitions() -> List[Partition]
```

Get status of alarm partitions

<a id="ksenia_lares.base_api.BaseApi.get_scenarios"></a>

#### get\_scenarios

```python
@abstractmethod
async def get_scenarios() -> List[Scenario]
```

Get status of scenarios

