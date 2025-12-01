import json
import os

CONFIG_CHILLERS = "config_chillers.json"
CONFIG_POWER = "config_power.json"


def save_chillers(data: dict):
    with open(CONFIG_CHILLERS, "w") as f:
        json.dump(data, f, indent=2)


def save_power(data: dict):
    with open(CONFIG_POWER, "w") as f:
        json.dump(data, f, indent=2)


def _ensure_chillers():
    if os.path.exists(CONFIG_CHILLERS):
        with open(CONFIG_CHILLERS, "r") as f:
            return json.load(f)

    # Auto-create 30 chillers
    chillers = []
    for i in range(1, 31):
        chillers.append(
            {
                "name": f"CH-{i}",
                "status": "OFF",
                "setpoint": 21.0,
            }
        )
    data = {"chillers": chillers}
    save_chillers(data)
    return data


def _ensure_power():
    if os.path.exists(CONFIG_POWER):
        with open(CONFIG_POWER, "r") as f:
            return json.load(f)

    transformers = [{"name": f"TR{i}", "status": "ON"} for i in range(1, 11)]
    ups = [{"name": f"UPS{i}", "status": "ON"} for i in range(1, 6)]
    genset = [{"name": f"G{i}", "status": "OFF"} for i in range(1, 11)]

    data = {"transformers": transformers, "ups": ups, "genset": genset}
    save_power(data)
    return data


def load_chillers():
    return _ensure_chillers()


def load_power():
    return _ensure_power()
