from simulator import simulate_chiller
from utils import load_chillers, save_chillers


def get_chiller_data():
    return load_chillers()


def toggle_chiller(data, idx):
    data["chillers"][idx]["status"] = (
        "OFF" if data["chillers"][idx]["status"] == "ON" else "ON"
    )
    save_chillers(data)
    return data


def update_setpoint(data, idx, new_sp):
    data["chillers"][idx]["setpoint"] = new_sp
    save_chillers(data)
    return data
