# ksenia-lares
Unofficial Python module designed to interact with the Ksenia Lares alarm system via API. 

## Features
- Supports IP series (Ksenia Lares 16 IP, 48 IP & 128 IP)
- NO SUPPORT FOR Ksenia Lares 4.0 currently
- Fetch alarm system info (e.g., name, version, MAC address).
- Retrieve and manage zone statuses.
- Activate scenarios and partitions.
- Bypass zones as needed.

## Installation
### Install from Source

Clone the repository and install locally:

```bash
git clone https://github.com/yourusername/ksenia_lares.git
cd ksenia_lares
pip install .
```

## Usage
### Example

```python
import asyncio
from ksenia_lares.ip_api import IpAPI

async def main():
    config = {
        "username": "your_username",
        "password": "your_password",
        "host": "192.168.1.1",
        "port": 8080,
    }

    api = IpAPI(config)

    # Fetch alarm system info
    info = await api.info()
    print("Alarm Info:", info)

    # Retrieve zone statuses
    zones = await api.get_zones()
    for zone in zones:
        print(f"Zone {zone.id}: {zone.status}")

    # Activate a scenario
    success = await api.activate_scenario(scenario=1, code="1234")
    print("Scenario Activated:", success)

asyncio.run(main())
```

## Contribution
### Getting Started
To contribute to this project, follow these steps:

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ksenia_lares.git
cd ksenia_lares
```
2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  
# On Windows: venv\Scripts\activate
```
3. Install dependencies:
```bash
pip install -e '.[dev]'
```
4. Run tests to ensure everything is working:
```bash
pytest
```

## License
This project is licensed under the MIT License. See the [LICENCE](LICENSE) file for details.