import re
import streamlit as st

from chiller_manager import get_chiller_data, toggle_chiller, update_setpoint
from power_manager import (
    get_power_data,
    toggle_transformer,
    toggle_ups,
    toggle_genset,
    toggle_pahu,
)
from simulator import (
    simulate_chiller,
    simulate_transformer,
    simulate_ups,
    simulate_genset,
    simulate_pahu,
)
from voice_agent import transcribe_voice, tts_voice
from utils import save_chillers, save_power
from alarms_agent import get_simulated_alarms, explain_alarm


# -------------------------------------------------------------
# Page config (dark)
# -------------------------------------------------------------
st.set_page_config(
    page_title="BMS AI Agent – MANISH SINGH",
    page_icon="BMS",
    layout="wide",
)


# -------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------
def status_badge(status: str) -> str:
    """Small pill badge for text explanations."""
    color = "#16d916" if status == "ON" else "#ff4d4d"
    return (
        "<span style='background:{}; padding:3px 10px; "
        "border-radius:12px; color:white; font-weight:bold;'>{}</span>".format(
            color, status
        )
    )


def status_cell(status: str) -> str:
    """Coloured table cell like PAHU ON/OFF bar."""
    color = "#16d916" if status == "ON" else "#ff4d4d"
    return (
        "<div style='background:{};color:white;text-align:center;"
        "padding:4px 6px;font-size:11px;font-weight:bold;"
        "border:1px solid #1f2937;'>{}</div>".format(color, status)
    )


def val(d: dict, key: str, default: float = 0.0) -> float:
    """
    Safe numeric lookup from simulation dicts.
    Avoids KeyError if key names differ slightly between simulators.
    """
    v = d.get(key, default)
    try:
        return float(v)
    except Exception:
        return float(default)


def voice_agent_handle_command(text: str, chillers_data: dict, power_data: dict):
    """
    Rule-based agent that understands simple natural language control:
      - 'turn on chiller 5'
      - 'set chiller 3 setpoint to 20'
      - 'turn off transformer 2'
      - 'start genset 3'
      - 'switch off ups 1'
    Returns:
        reply_text, updated_chillers_data, updated_power_data
    """
    t = text.lower()
    reply = []

    # ---------------- CHILLERS ----------------
    if "chiller" in t:
        m = re.search(r"chiller\s+(\d+)", t)
        if m:
            idx = int(m.group(1)) - 1
            chillers = chillers_data["chillers"]
            if 0 <= idx < len(chillers):
                ch = chillers[idx]
                if "setpoint" in t or "temperature" in t:
                    m_sp = re.search(r"(\d+(\.\d+)?)", t)
                    if m_sp:
                        new_sp = float(m_sp.group(1))
                        update_setpoint(chillers_data, idx, new_sp)
                        reply.append(
                            "Setpoint for {} updated to {:.1f} C.".format(
                                ch["name"], new_sp
                            )
                        )
                elif "on" in t or "start" in t:
                    ch["status"] = "ON"
                    reply.append("{} turned ON.".format(ch["name"]))
                elif "off" in t or "stop" in t:
                    ch["status"] = "OFF"
                    reply.append("{} turned OFF.".format(ch["name"]))
                else:
                    ch["status"] = "OFF" if ch["status"] == "ON" else "ON"
                    reply.append("Toggled {} to {}.".format(ch["name"], ch["status"]))
            else:
                reply.append("Chiller index out of range.")

    # ---------------- TRANSFORMERS ----------------
    if "transformer" in t or re.search(r"\btr\s*\d+", t):
        m = re.search(r"(transformer|tr)\s*([0-9]+)", t)
        if m:
            idx = int(m.group(2)) - 1
            trs = power_data["transformers"]
            if 0 <= idx < len(trs):
                tr = trs[idx]
                if "on" in t:
                    tr["status"] = "ON"
                    reply.append("{} turned ON.".format(tr["name"]))
                elif "off" in t:
                    tr["status"] = "OFF"
                    reply.append("{} turned OFF.".format(tr["name"]))
                else:
                    tr["status"] = "OFF" if tr["status"] == "ON" else "ON"
                    reply.append("Toggled {} to {}.".format(tr["name"], tr["status"]))

    # ---------------- UPS ----------------
    if "ups" in t:
        m = re.search(r"ups\s*([0-9]+)", t)
        if m:
            idx = int(m.group(1)) - 1
            ups_list = power_data["ups"]
            if 0 <= idx < len(ups_list):
                u = ups_list[idx]
                if "on" in t:
                    u["status"] = "ON"
                    reply.append("{} turned ON.".format(u["name"]))
                elif "off" in t:
                    u["status"] = "OFF"
                    reply.append("{} turned OFF.".format(u["name"]))
                else:
                    u["status"] = "OFF" if u["status"] == "ON" else "ON"
                    reply.append("Toggled {} to {}.".format(u["name"], u["status"]))

    # ---------------- GENSETS ----------------
    if "genset" in t or re.search(r"\bg\s*[0-9]+", t):
        m = re.search(r"(genset|g)\s*([0-9]+)", t)
        if m:
            idx = int(m.group(2)) - 1
            gens = power_data["genset"]
            if 0 <= idx < len(gens):
                g = gens[idx]
                if "on" in t or "start" in t:
                    g["status"] = "ON"
                    reply.append("{} started.".format(g["name"]))
                elif "off" in t or "stop" in t:
                    g["status"] = "OFF"
                    reply.append("{} stopped.".format(g["name"]))
                else:
                    g["status"] = "OFF" if g["status"] == "ON" else "ON"
                    reply.append("Toggled {} to {}.".format(g["name"], g["status"]))

    # ---------------- PAHU ----------------
    if "pahu" in t:
        m = re.search(r"pahu\s*([0-9]+)", t)
        if m:
            idx = int(m.group(1)) - 1
            pahu_list = power_data["pahu"]
            if 0 <= idx < len(pahu_list):
                p = pahu_list[idx]
                if "on" in t or "start" in t:
                    p["status"] = "ON"
                    reply.append("{} turned ON.".format(p["name"]))
                elif "off" in t or "stop" in t:
                    p["status"] = "OFF"
                    reply.append("{} turned OFF.".format(p["name"]))
                else:
                    p["status"] = "OFF" if p["status"] == "ON" else "ON"
                    reply.append("Toggled {} to {}.".format(p["name"], p["status"]))

    if not reply:
        reply.append(
            "I understood the text but could not map it to any control action."
        )

    # persist
    save_chillers(chillers_data)
    save_power(power_data)

    return " ".join(reply), chillers_data, power_data


# -------------------------------------------------------------
# Sidebar navigation
# -------------------------------------------------------------
menu = st.sidebar.radio(
    " Navigation",
    ["Chillers", "Power Control", "Voice Assistant", "Alarms & Events"],
    index=0,
    key="nav_main_radio",
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "<div style='color:#9fa6b2;font-size:13px;'>Dark BMS UI - Manish Singh</div>",
    unsafe_allow_html=True,
)


# -------------------------------------------------------------
# CHILLER DASHBOARD – 30 chillers, 3×10 grid
# -------------------------------------------------------------
if menu == "Chillers":
    st.header("Chiller Plant - 30 Units (3 x 10 Grid)")

    chillers_data = get_chiller_data()
    chillers = chillers_data["chillers"]

    num_chillers = len(chillers)
    chillers_per_row = 10
    num_rows = (num_chillers + chillers_per_row - 1) // chillers_per_row

    for row in range(num_rows):
        cols = st.columns(chillers_per_row)
        for col_idx in range(chillers_per_row):
            idx = row * chillers_per_row + col_idx
            if idx >= num_chillers:
                continue

            ch = chillers[idx]
            sim = simulate_chiller(ch)

            name = ch.get("name", "CH-{:02d}".format(idx + 1))
            status = ch.get("status", "OFF")
            sp = float(ch.get("setpoint", 22.0))

            supply = val(sim, "supply_temp", val(sim, "supply_air_temp", 0.0))
            inlet = val(sim, "inlet_temp", 0.0)
            outlet = val(sim, "outlet_temp", 0.0)
            ambient = val(sim, "ambient_temp", 0.0)
            comp1 = val(sim, "comp1", 0.0)
            comp2 = val(sim, "comp2", 0.0)
            power_kw = val(sim, "power_kw", val(sim, "power", 0.0))
            flow = val(sim, "water_flow", val(sim, "flow", 0.0))

            col = cols[col_idx]

            # blue header
            col.markdown(
                "<div style='background:#004b80;color:white;text-align:center;"
                "padding:4px;font-size:12px;font-weight:bold;'>{}</div>".format(
                    name
                ),
                unsafe_allow_html=True,
            )

            # status bar
            color = "#00aa00" if status == "ON" else "#aa0000"
            col.markdown(
                "<div style='background:{};color:white;text-align:center;"
                "padding:4px;font-size:12px;'>STATUS: {}</div>".format(
                    color, status
                ),
                unsafe_allow_html=True,
            )

            # data panel
            col.markdown(
                """
                <div style='background:#111;padding:6px;font-size:11px;color:#ddd;'>
                    <b>Setpoint:</b> {:.1f} C<br>
                    <b>Supply:</b> {:.1f} C<br>
                    <b>Inlet:</b> {:.1f} C<br>
                    <b>Outlet:</b> {:.1f} C<br>
                    <b>Ambient:</b> {:.1f} C<br>
                    <b>Comp-1:</b> {:.0f} %<br>
                    <b>Comp-2:</b> {:.0f} %<br>
                    <b>Power:</b> {:.1f} kW<br>
                    <b>Flow:</b> {:.1f} m3/hr<br>
                </div>
                """.format(
                    sp,
                    supply,
                    inlet,
                    outlet,
                    ambient,
                    comp1,
                    comp2,
                    power_kw,
                    flow,
                ),
                unsafe_allow_html=True,
            )

            if col.button(
                "Toggle {}".format(name),
                key="btn_chiller_toggle_{}".format(idx),
            ):
                toggle_chiller(chillers_data, idx)
                save_chillers(chillers_data)
                st.rerun()

            new_sp = col.number_input(
                "SP {}".format(name),
                min_value=16.0,
                max_value=26.0,
                value=float(sp),
                step=0.1,
                key="num_chiller_sp_{}".format(idx),
            )
            if abs(new_sp - sp) > 1e-4:
                update_setpoint(chillers_data, idx, float(new_sp))
                save_chillers(chillers_data)


# -------------------------------------------------------------
# POWER CONTROL – PAHU-style matrix layout
# -------------------------------------------------------------
elif menu == "Power Control":
    st.title("Power Control - Transformers / UPS / Genset / PAHU")

    power = get_power_data()

    # TRANSFORMERS
    st.subheader("Transformers")

    tr_list = power["transformers"]
    tr_sims = [simulate_transformer(tr) for tr in tr_list]

    html_tr = []
    html_tr.append(
        "<div style='background:#020617;padding:8px;border-radius:8px;"
        "border:1px solid #1f2937;margin-bottom:16px;'>"
    )
    html_tr.append(
        "<table style='border-collapse:collapse;width:100%;font-size:11px;'>"
    )

    html_tr.append("<tr>")
    html_tr.append(
        "<th style='background:#1f2937;color:#e5e7eb;padding:4px 6px;"
        "border:1px solid #111827;text-align:left;'>PARAMETERS</th>"
    )
    for tr in tr_list:
        html_tr.append(
            "<th style='background:#1d4ed8;color:white;padding:4px 6px;"
            "border:1px solid #111827;text-align:center;'>{}</th>".format(
                tr["name"]
            )
        )
    html_tr.append("</tr>")

    # status row
    html_tr.append("<tr>")
    html_tr.append(
        "<td style='background:#111827;color:#e5e7eb;padding:4px 6px;"
        "border:1px solid #1f2937;font-weight:bold;'>UNIT STATUS</td>"
    )
    for tr in tr_list:
        html_tr.append("<td>{}</td>".format(status_cell(tr["status"])))
    html_tr.append("</tr>")

    # voltage
    html_tr.append("<tr>")
    html_tr.append(
        "<td style='background:#111827;color:#e5e7eb;padding:4px 6px;"
        "border:1px solid #1f2937;font-weight:bold;'>VOLTAGE (V)</td>"
    )
    for sim in tr_sims:
        html_tr.append(
            "<td style='background:#020617;color:#e5e7eb;padding:4px 6px;"
            "border:1px solid #1f2937;text-align:center;'>{:.1f}</td>".format(
                val(sim, "voltage")
            )
        )
    html_tr.append("</tr>")

    # current
    html_tr.append("<tr>")
    html_tr.append(
        "<td style='background:#111827;color:#e5e7eb;padding:4px 6px;"
        "border:1px solid #1f2937;font-weight:bold;'>CURRENT (A)</td>"
    )
    for sim in tr_sims:
        html_tr.append(
            "<td style='background:#020617;color:#e5e7eb;padding:4px 6px;"
            "border:1px solid #1f2937;text-align:center;'>{:.1f}</td>".format(
                val(sim, "current")
            )
        )
    html_tr.append("</tr>")

    # power
    html_tr.append("<tr>")
    html_tr.append(
        "<td style='background:#111827;color:#e5e7eb;padding:4px 6px;"
        "border:1px solid #1f2937;font-weight:bold;'>POWER (kW)</td>"
    )
    for sim in tr_sims:
        html_tr.append(
            "<td style='background:#020617;color:#e5e7eb;padding:4px 6px;"
            "border:1px solid #1f2937;text-align:center;'>{:.2f}</td>".format(
                val(sim, "power")
            )
        )
    html_tr.append("</tr>")

    html_tr.append("</table></div>")
    st.markdown("".join(html_tr), unsafe_allow_html=True)

    tr_cols = st.columns(len(tr_list))
    for i, tr in enumerate(tr_list):
        if tr_cols[i].button(
            "Toggle {}".format(tr["name"]),
            key="btn_power_tr_{}".format(i),
        ):
            toggle_transformer(power, i)
            save_power(power)
            st.rerun()

    st.markdown("---")

    # UPS
    st.subheader("UPS")

    ups_list = power["ups"]
    ups_sims = [simulate_ups(u) for u in ups_list]

    html_ups = []
    html_ups.append(
        "<div style='background:#020617;padding:8px;border-radius:8px;"
        "border:1px solid #1f2937;margin-bottom:16px;'>"
    )
    html_ups.append(
        "<table style='border-collapse:collapse;width:100%;font-size:11px;'>"
    )

    html_ups.append("<tr>")
    html_ups.append(
        "<th style='background:#1f2937;color:#e5e7eb;padding:4px 6px;"
        "border:1px solid #111827;text-align:left;'>PARAMETERS</th>"
    )
    for u in ups_list:
        html_ups.append(
            "<th style='background:#1d4ed8;color:white;padding:4px 6px;"
            "border:1px solid #111827;text-align:center;'>{}</th>".format(
                u["name"]
            )
        )
    html_ups.append("</tr>")

    # status
    html_ups.append("<tr>")
    html_ups.append(
        "<td style='background:#111827;color:#e5e7eb;padding:4px 6px;"
        "border:1px solid #1f2937;font-weight:bold;'>UNIT STATUS</td>"
    )
    for u in ups_list:
        html_ups.append("<td>{}</td>".format(status_cell(u["status"])))
    html_ups.append("</tr>")

    # voltage
    html_ups.append("<tr>")
    html_ups.append(
        "<td style='background:#111827;color:#e5e7eb;padding:4px 6px;"
        "border:1px solid #1f2937;font-weight:bold;'>VOLTAGE (V)</td>"
    )
    for sim in ups_sims:
        html_ups.append(
            "<td style='background:#020617;color:#e5e7eb;padding:4px 6px;"
            "border:1px solid #1f2937;text-align:center;'>{:.1f}</td>".format(
                val(sim, "voltage")
            )
        )
    html_ups.append("</tr>")

    # current
    html_ups.append("<tr>")
    html_ups.append(
        "<td style='background:#111827;color:#e5e7eb;padding:4px 6px;"
        "border:1px solid #1f2937;font-weight:bold;'>CURRENT (A)</td>"
    )
    for sim in ups_sims:
        html_ups.append(
            "<td style='background:#020617;color:#e5e7eb;padding:4px 6px;"
            "border:1px solid #1f2937;text-align:center;'>{:.1f}</td>".format(
                val(sim, "current")
            )
        )
    html_ups.append("</tr>")

    # power
    html_ups.append("<tr>")
    html_ups.append(
        "<td style='background:#111827;color:#e5e7eb;padding:4px 6px;"
        "border:1px solid #1f2937;font-weight:bold;'>POWER (kW)</td>"
    )
    for sim in ups_sims:
        html_ups.append(
            "<td style='background:#020617;color:#e5e7eb;padding:4px 6px;"
            "border:1px solid #1f2937;text-align:center;'>{:.2f}</td>".format(
                val(sim, "power")
            )
        )
    html_ups.append("</tr>")

    # load
    html_ups.append("<tr>")
    html_ups.append(
        "<td style='background:#111827;color:#e5e7eb;padding:4px 6px;"
        "border:1px solid #1f2937;font-weight:bold;'>LOAD (%)</td>"
    )
    for sim in ups_sims:
        html_ups.append(
            "<td style='background:#020617;color:#e5e7eb;padding:4px 6px;"
            "border:1px solid #1f2937;text-align:center;'>{:.1f}</td>".format(
                val(sim, "load")
            )
        )
    html_ups.append("</tr>")

    html_ups.append("</table></div>")
    st.markdown("".join(html_ups), unsafe_allow_html=True)

    ups_cols = st.columns(len(ups_list))
    for i, u in enumerate(ups_list):
        if ups_cols[i].button(
            "Toggle {}".format(u["name"]),
            key="btn_power_ups_{}".format(i),
        ):
            toggle_ups(power, i)
            save_power(power)
            st.rerun()

    st.markdown("---")

    # GENSETS
    st.subheader("Gensets")

    g_list = power["genset"]
    g_sims = [simulate_genset(g) for g in g_list]

    html_g = []
    html_g.append(
        "<div style='background:#020617;padding:8px;border-radius:8px;"
        "border:1px solid #1f2937;margin-bottom:16px;'>"
    )
    html_g.append(
        "<table style='border-collapse:collapse;width:100%;font-size:11px;'>"
    )

    html_g.append("<tr>")
    html_g.append(
        "<th style='background:#1f2937;color:#e5e7eb;padding:4px 6px;"
        "border:1px solid #111827;text-align:left;'>PARAMETERS</th>"
    )
    for g in g_list:
        html_g.append(
            "<th style='background:#1d4ed8;color:white;padding:4px 6px;"
            "border:1px solid #111827;text-align:center;'>{}</th>".format(
                g["name"]
            )
        )
    html_g.append("</tr>")

    # status
    html_g.append("<tr>")
    html_g.append(
        "<td style='background:#111827;color:#e5e7eb;padding:4px 6px;"
        "border:1px solid #1f2937;font-weight:bold;'>UNIT STATUS</td>"
    )
    for g in g_list:
        html_g.append("<td>{}</td>".format(status_cell(g["status"])))
    html_g.append("</tr>")

    # voltage
    html_g.append("<tr>")
    html_g.append(
        "<td style='background:#111827;color:#e5e7eb;padding:4px 6px;"
        "border:1px solid #1f2937;font-weight:bold;'>VOLTAGE (V)</td>"
    )
    for sim in g_sims:
        html_g.append(
            "<td style='background:#020617;color:#e5e7eb;padding:4px 6px;"
            "border:1px solid #1f2937;text-align:center;'>{:.1f}</td>".format(
                val(sim, "voltage")
            )
        )
    html_g.append("</tr>")

    # current
    html_g.append("<tr>")
    html_g.append(
        "<td style='background:#111827;color:#e5e7eb;padding:4px 6px;"
        "border:1px solid #1f2937;font-weight:bold;'>CURRENT (A)</td>"
    )
    for sim in g_sims:
        html_g.append(
            "<td style='background:#020617;color:#e5e7eb;padding:4px 6px;"
            "border:1px solid #1f2937;text-align:center;'>{:.1f}</td>".format(
                val(sim, "current")
            )
        )
    html_g.append("</tr>")

    # power
    html_g.append("<tr>")
    html_g.append(
        "<td style='background:#111827;color:#e5e7eb;padding:4px 6px;"
        "border:1px solid #1f2937;font-weight:bold;'>POWER (kW)</td>"
    )
    for sim in g_sims:
        html_g.append(
            "<td style='background:#020617;color:#e5e7eb;padding:4px 6px;"
            "border:1px solid #1f2937;text-align:center;'>{:.2f}</td>".format(
                val(sim, "power")
            )
        )
    html_g.append("</tr>")

    # load
    html_g.append("<tr>")
    html_g.append(
        "<td style='background:#111827;color:#e5e7eb;padding:4px 6px;"
        "border:1px solid #1f2937;font-weight:bold;'>LOAD (%)</td>"
    )
    for sim in g_sims:
        html_g.append(
            "<td style='background:#020617;color:#e5e7eb;padding:4px 6px;"
            "border:1px solid #1f2937;text-align:center;'>{:.1f}</td>".format(
                val(sim, "load")
            )
        )
    html_g.append("</tr>")

    html_g.append("</table></div>")
    st.markdown("".join(html_g), unsafe_allow_html=True)

    g_cols = st.columns(len(g_list))
    for i, g in enumerate(g_list):
        if g_cols[i].button(
            "Toggle {}".format(g["name"]),
            key="btn_power_gen_{}".format(i),
        ):
            toggle_genset(power, i)
            save_power(power)
            st.rerun()

    st.markdown("---")

    # PAHU
    st.subheader("PAHU Units")

    p_list = power["pahu"]
    p_sims = [simulate_pahu(p) for p in p_list]

    html_p = []
    html_p.append(
        "<div style='background:#020617;padding:8px;border-radius:8px;"
        "border:1px solid #1f2937;margin-bottom:16px;'>"
    )
    html_p.append(
        "<table style='border-collapse:collapse;width:100%;font-size:11px;'>"
    )

    html_p.append("<tr>")
    html_p.append(
        "<th style='background:#1f2937;color:#e5e7eb;padding:4px 6px;"
        "border:1px solid #111827;text-align:left;'>PARAMETERS</th>"
    )
    for p in p_list:
        html_p.append(
            "<th style='background:#1d4ed8;color:white;padding:4px 6px;"
            "border:1px solid #111827;text-align:center;'>{}</th>".format(
                p["name"]
            )
        )
    html_p.append("</tr>")

    # status
    html_p.append("<tr>")
    html_p.append(
        "<td style='background:#111827;color:#e5e7eb;padding:4px 6px;"
        "border:1px solid #1f2937;font-weight:bold;'>UNIT STATUS</td>"
    )
    for p in p_list:
        html_p.append("<td>{}</td>".format(status_cell(p["status"])))
    html_p.append("</tr>")

    # supply air temp
    html_p.append("<tr>")
    html_p.append(
        "<td style='background:#111827;color:#e5e7eb;padding:4px 6px;"
        "border:1px solid #1f2937;font-weight:bold;'>SUPPLY AIR TEMP (C)</td>"
    )
    for sim in p_sims:
        html_p.append(
            "<td style='background:#020617;color:#e5e7eb;padding:4px 6px;"
            "border:1px solid #1f2937;text-align:center;'>{:.1f}</td>".format(
                val(sim, "supply_air_temp")
            )
        )
    html_p.append("</tr>")

    # return air temp
    html_p.append("<tr>")
    html_p.append(
        "<td style='background:#111827;color:#e5e7eb;padding:4px 6px;"
        "border:1px solid #1f2937;font-weight:bold;'>RETURN AIR TEMP (C)</td>"
    )
    for sim in p_sims:
        html_p.append(
            "<td style='background:#020617;color:#e5e7eb;padding:4px 6px;"
            "border:1px solid #1f2937;text-align:center;'>{:.1f}</td>".format(
                val(sim, "return_air_temp")
            )
        )
    html_p.append("</tr>")

    # airflow
    html_p.append("<tr>")
    html_p.append(
        "<td style='background:#111827;color:#e5e7eb;padding:4px 6px;"
        "border:1px solid #1f2937;font-weight:bold;'>AIRFLOW (CFM)</td>"
    )
    for sim in p_sims:
        html_p.append(
            "<td style='background:#020617;color:#e5e7eb;padding:4px 6px;"
            "border:1px solid #1f2937;text-align:center;'>{:.0f}</td>".format(
                val(sim, "airflow")
            )
        )
    html_p.append("</tr>")

    # power
    html_p.append("<tr>")
    html_p.append(
        "<td style='background:#111827;color:#e5e7eb;padding:4px 6px;"
        "border:1px solid #1f2937;font-weight:bold;'>POWER (kW)</td>"
    )
    for sim in p_sims:
        html_p.append(
            "<td style='background:#020617;color:#e5e7eb;padding:4px 6px;"
            "border:1px solid #1f2937;text-align:center;'>{:.2f}</td>".format(
                val(sim, "power")
            )
        )
    html_p.append("</tr>")

    # filter dp
    html_p.append("<tr>")
    html_p.append(
        "<td style='background:#111827;color:#e5e7eb;padding:4px 6px;"
        "border:1px solid #1f2937;font-weight:bold;'>FILTER DP (in-wg)</td>"
    )
    for sim in p_sims:
        html_p.append(
            "<td style='background:#020617;color:#e5e7eb;padding:4px 6px;"
            "border:1px solid #1f2937;text-align:center;'>{:.2f}</td>".format(
                val(sim, "filter_dp")
            )
        )
    html_p.append("</tr>")

    html_p.append("</table></div>")
    st.markdown("".join(html_p), unsafe_allow_html=True)

    p_cols = st.columns(len(p_list))
    for i, p in enumerate(p_list):
        if p_cols[i].button(
            "Toggle {}".format(p["name"]),
            key="btn_power_pahu_{}".format(i),
        ):
            toggle_pahu(power, i)
            save_power(power)
            st.rerun()


# -------------------------------------------------------------
# VOICE ASSISTANT
# -------------------------------------------------------------
elif menu == "Voice Assistant":
    st.title("Voice Assistant - Free STT and TTS")

    st.write(
        "Upload a short WAV file with a command such as: "
        "'turn on chiller 5', 'set chiller 3 setpoint to 20', "
        "'turn off transformer 2', 'turn on genset 4', 'turn off ups 1'."
    )

    audio_file = st.file_uploader(
        "Upload WAV file (16-bit PCM recommended)",
        type=["wav"],
        key="voice_audio_uploader",
    )

    if audio_file is not None:
        raw_bytes = audio_file.read()
        with st.spinner("Transcribing voice command..."):
            text = transcribe_voice(raw_bytes)

        if not text:
            st.error("No speech recognized or STT error. Try again.")
        else:
            st.success("Recognized text: {}".format(text))

            chillers_data = get_chiller_data()
            power_data = get_power_data()

            reply_text, chillers_data, power_data = voice_agent_handle_command(
                text, chillers_data, power_data
            )

            st.info("Agent reply: {}".format(reply_text))

            with st.spinner("Generating spoken reply..."):
                out_audio = tts_voice(reply_text)

            st.audio(out_audio, format="audio/mp3", key="voice_audio_player")


# -------------------------------------------------------------
# ALARMS & EVENTS
# -------------------------------------------------------------
elif menu == "Alarms & Events":
    st.title("Alarms and Events - BMS AI Explain")

    st.write(
        "Simulated BMS alarms from chillers, transformers, UPS, "
        "gensets and environment. A rule-based engine explains root "
        "cause and recommended action."
    )

    alarms = get_simulated_alarms()

    col1, col2 = st.columns(2)
    with col1:
        system_filter = st.selectbox(
            "Filter by system",
            options=["All", "Chiller", "Power", "UPS", "Genset", "Environment"],
            index=0,
            key="alarm_filter_system",
        )
    with col2:
        severity_filter = st.selectbox(
            "Filter by severity",
            options=["All", "Critical", "Major", "Minor", "Info"],
            index=0,
            key="alarm_filter_severity",
        )

    filtered = []
    for al in alarms:
        if system_filter != "All" and al["system"] != system_filter:
            continue
        if severity_filter != "All" and al["severity"] != severity_filter:
            continue
        filtered.append(al)

    if not filtered:
        st.info("No alarms matching the selected filters.")
    else:
        for al in filtered:
            explanation = explain_alarm(al)

            sev = al["severity"]
            if sev == "Critical":
                sev_color = "#f97373"
            elif sev == "Major":
                sev_color = "#facc15"
            elif sev == "Minor":
                sev_color = "#4ade80"
            else:
                sev_color = "#60a5fa"

            st.markdown(
                """
                <div style='background:#111827; padding:14px; border-radius:10px;
                            border:1px solid #1f2937; margin-bottom:12px;'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <div>
                            <span style='color:#9ca3af; font-size:12px;'>Time</span>
                            <div style='color:#e5e7eb; font-size:13px;'>{timestamp}</div>
                        </div>
                        <div>
                            <span style='color:#9ca3af; font-size:12px;'>Severity</span><br>
                            <span style='color:{sev_color}; font-weight:bold;'>{severity}</span>
                        </div>
                        <div>
                            <span style='color:#9ca3af; font-size:12px;'>System</span>
                            <div style='color:#e5e7eb; font-size:13px;'>{system}</div>
                        </div>
                        <div>
                            <span style='color:#9ca3af; font-size:12px;'>Source</span>
                            <div style='color:#e5e7eb; font-size:13px;'>{source}</div>
                        </div>
                    </div>
                    <hr style='border:1px solid #1f2937; margin-top:8px; margin-bottom:8px;'>
                    <div style='color:#e5e7eb; font-size:14px;'>
                        <b>Alarm:</b> {message}
                    </div>
                    <div style='margin-top:6px; color:#fbbf24; font-size:13px;'>
                        <b>Probable root cause:</b> {root}</div>
                    <div style='margin-top:4px; color:#93c5fd; font-size:13px;'>
                        <b>Recommended action:</b> {action}</div>
                </div>
                """.format(
                    timestamp=al["timestamp"],
                    sev_color=sev_color,
                    severity=al["severity"],
                    system=al["system"],
                    source=al["source"],
                    message=al["message"],
                    root=explanation["root_cause"],
                    action=explanation["action"],
                ),
                unsafe_allow_html=True,
            )
