import json
import os

CONFIG_CHILLERS = "config_chillers.json"
CONFIG_POWER = "config_power.json"


def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def load_chillers():
    data = load_json(CONFIG_CHILLERS)
    return data


def save_chillers(data):
    save_json(CONFIG_CHILLERS, data)


def load_power():
    data = load_json(CONFIG_POWER)
    return data


def save_power(data):
    save_json(CONFIG_POWER, data)
