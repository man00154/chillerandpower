import datetime
import random


def _now_minus_minutes(m: int) -> str:
    """Return timestamp string m minutes in the past."""
    ts = datetime.datetime.now() - datetime.timedelta(minutes=m)
    return ts.strftime("%Y-%m-%d %H:%M:%S")


def get_simulated_alarms():
    """
    Return a list of simulated BMS alarms for the data center.
    Each alarm is a dict with:
      - timestamp
      - severity
      - system  (Chiller / Power / UPS / Genset / Environment)
      - source  (device name)
      - message (alarm text)
    """
    base_alarms = [
        {
            "minutes_ago": 2,
            "severity": "Critical",
            "system": "Chiller",
            "source": "CH-5",
            "message": "High chilled water return temperature at CH-5 (above 18°C).",
        },
        {
            "minutes_ago": 5,
            "severity": "Major",
            "system": "Chiller",
            "source": "CH-2",
            "message": "Low delta-T across CH-2 evaporator loop.",
        },
        {
            "minutes_ago": 8,
            "severity": "Major",
            "system": "UPS",
            "source": "UPS3",
            "message": "UPS3 running on battery, input mains supply lost.",
        },
        {
            "minutes_ago": 11,
            "severity": "Critical",
            "system": "Power",
            "source": "TR2",
            "message": "Transformer TR2 overload – current above 110% rated.",
        },
        {
            "minutes_ago": 14,
            "severity": "Minor",
            "system": "Genset",
            "source": "G4",
            "message": "Genset G4 low fuel level warning.",
        },
        {
            "minutes_ago": 17,
            "severity": "Major",
            "system": "Environment",
            "source": "Server Hall L1",
            "message": "High server room temperature in Hall L1 (above 27°C).",
        },
        {
            "minutes_ago": 20,
            "severity": "Minor",
            "system": "Environment",
            "source": "PAHU-A2",
            "message": "PAHU-A2 filter differential pressure high – filter choking.",
        },
        {
            "minutes_ago": 24,
            "severity": "Info",
            "system": "Chiller",
            "source": "CH-10",
            "message": "CH-10 switched to standby mode after load sharing.",
        },
    ]

    alarms = []
    for a in base_alarms:
        alarms.append(
            {
                "timestamp": _now_minus_minutes(a["minutes_ago"]),
                "severity": a["severity"],
                "system": a["system"],
                "source": a["source"],
                "message": a["message"],
            }
        )

    # Optionally shuffle so they look dynamic
    random.shuffle(alarms)
    return alarms


def explain_alarm(alarm: dict) -> dict:
    """
    Rule-based 'AI' explanation engine.
    Takes an alarm dict and returns:
      {
        "root_cause": "...",
        "action": "..."
      }
    """
    msg = alarm["message"].lower()
    system = alarm["system"]
    source = alarm["source"]

    # ------- Chiller related -------
    if "high chilled water return" in msg or "high chilled water" in msg:
        return {
            "root_cause": (
                "Load on the chilled water loop is high or one of the coils/CRACs "
                "is not rejecting heat effectively. Return water is coming back too hot."
            ),
            "action": (
                f"Check IT load in corresponding zone, verify CH pump status and valve positions, "
                f"inspect CRAC/CRAH coil cleanliness and confirm {source} is running at required capacity."
            ),
        }

    if "low delta-t" in msg:
        return {
            "root_cause": (
                "Chiller is not getting enough heat transfer. Either flow is too high "
                "or coils are bypassing, causing poor temperature drop across evaporator."
            ),
            "action": (
                "Check chilled water balancing valves, verify 2-way/3-way valve positions, "
                "and optimize chiller flow setpoints. Investigate bypass lines kept open."
            ),
        }

    # ------- UPS related -------
    if "ups" in msg and "battery" in msg:
        return {
            "root_cause": (
                "Utility supply to this UPS is lost or unstable, causing it to run from battery."
            ),
            "action": (
                f"Check upstream panel feed to {source}, confirm breaker status, "
                "and verify remaining battery backup time. Prepare for controlled IT load shutdown "
                "if mains power is not restored."
            ),
        }

    # ------- Transformer related -------
    if "overload" in msg and "transformer" in msg:
        return {
            "root_cause": (
                "Total downstream load has exceeded transformer's rated capacity."
            ),
            "action": (
                f"Review active IT and mechanical loads fed by {source}, "
                "shed non-critical load, and redistribute feeders if redundancy is available."
            ),
        }

    # ------- Genset related -------
    if "low fuel" in msg and "genset" in msg:
        return {
            "root_cause": "Fuel level in genset day tank or main tank is below configured threshold.",
            "action": (
                f"Schedule refilling for {source} immediately. If genset is expected to auto-start "
                "on power failure, ensure fuel is replenished before any planned maintenance "
                "or grid instability."
            ),
        }

    # ------- Environment / HVAC -------
    if "high server room temperature" in msg:
        return {
            "root_cause": (
                "Cooling capacity in the affected hall is insufficient or airflow distribution is poor."
            ),
            "action": (
                "Check running status of CRAC/CRAH/PAHU units in that hall, verify setpoints and "
                "fan speeds, and inspect hot/cold aisle containment. Confirm no blocked floor tiles."
            ),
        }

    if "filter differential pressure high" in msg or "filter choking" in msg:
        return {
            "root_cause": (
                "Air filter across the unit is clogged, reducing airflow and increasing fan energy."
            ),
            "action": (
                f"Inspect and clean or replace filters on {source}. After replacement, "
                "reset the DP alarm and trend airflow/temperature for stability."
            ),
        }

    # ------- Standby / Info -------
    if "standby mode" in msg:
        return {
            "root_cause": (
                "Chiller has been taken to standby as part of load sharing or rotation policy."
            ),
            "action": (
                f"Verify that N+1 redundancy is intact after {source} moved to standby. "
                "No immediate action required unless plant capacity margin is low."
            ),
        }

    # ------- Generic fallback -------
    return {
        "root_cause": (
            "No specific rule matched. This appears to be a generic BMS event or OEM-specific alarm."
        ),
        "action": (
            "Check detailed alarm description in BMS/DCIM, consult OEM manual for this alarm code, "
            "and follow site SOP for triage and escalation."
        ),
    }
