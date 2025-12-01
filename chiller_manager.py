from utils import load_chillers, save_chillers


def get_chiller_data():
    return load_chillers()


def toggle_chiller(data: dict, idx: int):
    ch = data["chillers"][idx]
    ch["status"] = "OFF" if ch["status"] == "ON" else "ON"
    save_chillers(data)
    return data


def update_setpoint(data: dict, idx: int, new_sp: float):
    data["chillers"][idx]["setpoint"] = float(new_sp)
    save_chillers(data)
    return data
