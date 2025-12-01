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


def load_chillers() -> dict:
    """Load chillers config; if missing, auto-create 30 chillers."""
    if not os.path.exists(CONFIG_CHILLERS):
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

    with open(CONFIG_CHILLERS, "r") as f:
        return json.load(f)


def load_power() -> dict:
    """Load power config; if missing, auto-create 7 TR, 4 UPS, 7 G, 4 PAHU."""
    if not os.path.exists(CONFIG_POWER):
        transformers = [{"name": f"TR{i}", "status": "ON"} for i in range(1, 8)]
        ups = [{"name": f"UPS{i}", "status": "ON"} for i in range(1, 5)]
        genset = [{"name": f"G{i}", "status": "OFF"} for i in range(1, 8)]
        pahu = [{"name": f"PAHU{i}", "status": "ON"} for i in range(1, 5)]
        data = {
            "transformers": transformers,
            "ups": ups,
            "genset": genset,
            "pahu": pahu,
        }
        save_power(data)
        return data

    with open(CONFIG_POWER, "r") as f:
        return json.load(f)
