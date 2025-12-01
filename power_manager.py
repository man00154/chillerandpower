from utils import load_power, save_power


def get_power_data():
    return load_power()


def toggle_transformer(power_data: dict, idx: int):
    tr = power_data["transformers"][idx]
    tr["status"] = "OFF" if tr["status"] == "ON" else "ON"
    save_power(power_data)
    return power_data


def toggle_ups(power_data: dict, idx: int):
    u = power_data["ups"][idx]
    u["status"] = "OFF" if u["status"] == "ON" else "ON"
    save_power(power_data)
    return power_data


def toggle_genset(power_data: dict, idx: int):
    g = power_data["genset"][idx]
    g["status"] = "OFF" if g["status"] == "ON" else "ON"
    save_power(power_data)
    return power_data


def toggle_pahu(power_data: dict, idx: int):
    """Toggle PAHU ON/OFF."""
    p = power_data["pahu"][idx]
    p["status"] = "OFF" if p["status"] == "ON" else "ON"
    save_power(power_data)
    return power_data
