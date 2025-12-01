import random


# -------------------------
# CHILLER SIMULATION
# -------------------------
def simulate_chiller(ch):
    if ch["status"] == "OFF":
        return {
            "supply": 0,
            "inlet": 0,
            "outlet": 0,
            "ambient": 0,
            "comp1": 0,
            "comp2": 0,
            "power": 0,
            "flow": 0,
        }

    return {
        "supply": round(ch["setpoint"] + random.uniform(-1, 1), 2),
        "inlet": round(random.uniform(20, 28), 2),
        "outlet": round(random.uniform(18, 25), 2),
        "ambient": round(random.uniform(28, 32), 2),
        "comp1": round(random.uniform(40, 70), 2),
        "comp2": round(random.uniform(0, 70), 2),
        "power": round(random.uniform(200, 300), 2),
        "flow": round(random.uniform(200, 350), 2),
    }


# -------------------------
# POWER SIMULATION
# -------------------------
def simulate_transformer(tr):
    if tr["status"] == "OFF":
        return {
            "voltage": 0,
            "current": 0,
            "power": 0,
        }
    return {
        "voltage": round(random.uniform(410, 416), 2),
        "current": round(random.uniform(400, 1200), 2),
        "power": round(random.uniform(100, 800), 2),
    }


def simulate_ups(u):
    if u["status"] == "OFF":
        return {
            "voltage": 0,
            "current": 0,
            "power": 0,
            "load": 0,
        }
    return {
        "voltage": round(random.uniform(410, 416), 2),
        "current": round(random.uniform(50, 300), 2),
        "power": round(random.uniform(30, 150), 2),
        "load": round(random.uniform(5, 40), 2),
    }


def simulate_genset(g):
    if g["status"] == "OFF":
        return {
            "voltage": 0,
            "current": 0,
            "power": 0,
            "load": 0
        }
    return {
        "voltage": round(random.uniform(410, 416), 2),
        "current": round(random.uniform(30, 200), 2),
        "power": round(random.uniform(20, 150), 2),
        "load": round(random.uniform(5, 40), 2),
    }
