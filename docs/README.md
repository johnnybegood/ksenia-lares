<a id="ksenia_lares"></a>

# ksenia\_lares

Unofficial python API for the Ksenia Lares alarm.

- [B](base.md)

<a id="ksenia_lares.initialize"></a>

#### initialize

```python
def initialize(config: dict) -> BaseApi
```

Initialize API based on the API version and returns a [BaseApi](base.md) class for the given `api_version`:
- IP: Returns [IpApi](IP.md)
- 4: Not yet supported

**Arguments**:

- `config` _dict_ - A dictionary containing the following keys:
  - api_version (str): IP for IP range or 4 for Lares 4.0.


