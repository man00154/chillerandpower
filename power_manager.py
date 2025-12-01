from simulator import simulate_transformer, simulate_ups, simulate_genset
from utils import load_power, save_power


def get_power_data():
    return load_power()


def toggle_transformer(power_data, idx):
    power_data["transformers"][idx]["status"] = (
        "OFF" if power_data["transformers"][idx]["status"] == "ON" else "ON"
    )
    save_power(power_data)
    return power_data


def toggle_ups(power_data, idx):
    power_data["ups"][idx]["status"] = (
        "OFF" if power_data["ups"][idx]["status"] == "ON" else "ON"
    )
    save_power(power_data)
    return power_data


def toggle_genset(power_data, idx):
    power_data["genset"][idx]["status"] = (
        "OFF" if power_data["genset"][idx]["status"] == "ON" else "ON"
    )
    save_power(power_data)
    return power_data
