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
# Page config (dark style)
# -------------------------------------------------------------
st.set_page_config(
    page_title="BMS AI Agent – MANISH SINGH",
    layout="wide",
    page_icon="⚙️",
)


# -------------------------------------------------------------
# Common helpers
# -------------------------------------------------------------
def status_badge(status: str) -> str:
    """Return HTML badge for ON / OFF."""
    color = "#16d916" if status == "ON" else "#ff4d4d"
    return (
        f"<span style='background:{color}; padding:3px 10px; "
        f"border-radius:12px; color:white; font-weight:bold;'>{status}</span>"
    )


def voice_agent_handle_command(text: str, chillers_data: dict, power_data: dict):
    """
    Simple rule-based 'agent' that interprets commands like:
      - 'turn on chiller 5'
      - 'set chiller 3 setpoint to 20'
      - 'turn off transformer 2'
      - 'turn on genset 3'
      - 'switch off ups 1'
    and updates the configs accordingly.
    Returns (response_message, updated_chillers_data, updated_power_data).
    """
    t = text.lower()
    response_parts = []

    # ---------------- CHILLER CONTROL ----------------
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
                        response_parts.append(
                            f"Setpoint for {ch['name']} updated to {new_sp:.1f} °C."
                        )
                elif "on" in t:
                    ch["status"] = "ON"
                    response_parts.append(f"{ch['name']} turned ON.")
                elif "off" in t:
                    ch["status"] = "OFF"
                    response_parts.append(f"{ch['name']} turned OFF.")
                else:
                    ch["status"] = "OFF" if ch["status"] == "ON" else "ON"
                    response_parts.append(
                        f"Toggled {ch['name']} to {ch['status']}."
                    )
            else:
                response_parts.append("Chiller index out of range.")

    # ---------------- TRANSFORMER CONTROL ----------------
    if "transformer" in t or "tr" in t:
        m = re.search(r"(transformer|tr)\s*([0-9]+)", t)
        if m:
            idx = int(m.group(2)) - 1
            if 0 <= idx < len(power_data["transformers"]):
                tr = power_data["transformers"][idx]
                if "on" in t:
                    tr["status"] = "ON"
                    response_parts.append(f"{tr['name']} turned ON.")
                elif "off" in t:
                    tr["status"] = "OFF"
                    response_parts.append(f"{tr['name']} turned OFF.")
                else:
                    tr["status"] = "OFF" if tr["status"] == "ON" else "ON"
                    response_parts.append(
                        f"Toggled {tr['name']} to {tr['status']}."
                    )

    # ---------------- UPS CONTROL ----------------
    if "ups" in t:
        m = re.search(r"ups\s*([0-9]+)", t)
        if m:
            idx = int(m.group(1)) - 1
            if 0 <= idx < len(power_data["ups"]):
                u = power_data["ups"][idx]
                if "on" in t:
                    u["status"] = "ON"
                    response_parts.append(f"{u['name']} turned ON.")
                elif "off" in t:
                    u["status"] = "OFF"
                    response_parts.append(f"{u['name']} turned OFF.")
                else:
                    u["status"] = "OFF" if u["status"] == "ON" else "ON"
                    response_parts.append(
                        f"Toggled {u['name']} to {u['status']}."
                    )

    # ---------------- GENSET CONTROL ----------------
    if "genset" in t or re.search(r"\bg\s*[0-9]+", t):
        m = re.search(r"(genset|g)\s*([0-9]+)", t)
        if m:
            idx = int(m.group(2)) - 1
            if 0 <= idx < len(power_data["genset"]):
                g = power_data["genset"][idx]
                if "on" in t:
                    g["status"] = "ON"
                    response_parts.append(f"{g['name']} turned ON.")
                elif "off" in t:
                    g["status"] = "OFF"
                    response_parts.append(f"{g['name']} turned OFF.")
                else:
                    g["status"] = "OFF" if g["status"] == "ON" else "ON"
                    response_parts.append(
                        f"Toggled {g['name']} to {g['status']}."
                    )

    if not response_parts:
        response_parts.append(
            "I understood the text but could not map it to any control action."
        )

    # Save configs after modifications
    save_chillers(chillers_data)
    save_power(power_data)

    return " ".join(response_parts), chillers_data, power_data


# -------------------------------------------------------------
# Sidebar navigation
# -------------------------------------------------------------
menu = st.sidebar.radio(
    " Navigation",
    ["Chillers", "Power Control", "Voice Assistant", "Alarms & Events"],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "<div style='color:#9fa6b2;font-size:13px;'>Dark BMS UI • Manish Singh</div>",
    unsafe_allow_html=True,
)


# -------------------------------------------------------------
# CHILLER DASHBOARD – 30 chillers, 3×10 grid
# -------------------------------------------------------------
if menu == "Chillers":
    st.header("Chiller Plant – 30 Units (3 × 10 Grid)")

NUM_CHILLERS = 30
CHILLERS_PER_ROW = 10

for row in range(3):
    cols = st.columns(CHILLERS_PER_ROW)
    for col_idx in range(CHILLERS_PER_ROW):
        ch_id = row * CHILLERS_PER_ROW + col_idx + 1
        ch = config["chillers"][ch_id - 1]
        sim = simulate_chiller_readings(ch["setpoint"])
        col = cols[col_idx]

        # Blue header
        col.markdown(
            f"<div style='background:#004b80;color:white;text-align:center;"
            f"padding:4px;font-size:12px;font-weight:bold;'>CH-{ch_id:02d}</div>",
            unsafe_allow_html=True,
        )

        # Status bar
        color = "#00aa00" if ch["status"] == "ON" else "#aa0000"
        col.markdown(
            f"<div style='background:{color};color:white;text-align:center;"
            f"padding:4px;font-size:12px;'>STATUS: {ch['status']}</div>",
            unsafe_allow_html=True,
        )

        # Data panel
        col.markdown(
            f"""
            <div style='background:#111;padding:6px;font-size:11px;color:#ddd;'>
                <b>Setpoint:</b> {ch['setpoint']}°C<br>
                <b>Supply:</b> {sim['supply_temp']}°C<br>
                <b>Inlet:</b> {sim['inlet_temp']}°C<br>
                <b>Outlet:</b> {sim['outlet_temp']}°C<br>
                <b>Ambient:</b> {sim['ambient_temp']}°C<br>
                <b>Comp-1:</b> {sim['comp1']}%<br>
                <b>Comp-2:</b> {sim['comp2']}%<br>
                <b>Power:</b> {sim['power_kw']} kW<br>
                <b>Flow:</b> {sim['water_flow']} m³/hr<br>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Toggle button
        if col.button(f"Toggle CH-{ch_id}", key=f"toggle_{ch_id}"):
            ch["status"] = simulate_toggle_status(ch["status"])
            config["chillers"][ch_id - 1] = ch
            save_chiller_config(config)
            st.rerun()

        # Setpoint input
        new_sp = col.number_input(
            f"SP CH-{ch_id}", 16.0, 26.0, ch["setpoint"], 0.1,
            key=f"sp_{ch_id}"
        )
        if new_sp != ch["setpoint"]:
            ch["setpoint"] = new_sp
            config["chillers"][ch_id - 1] = ch
            save_chiller_config(config)

# -------------------------------------------------------------
# POWER CONTROL DASHBOARD – 7×1 TR, 7×1 G, 4×1 UPS, 4×1 PAHU
# -------------------------------------------------------------
elif menu == "Power Control":
    st.title(" Power Control")

    power = get_power_data()

    # -------------------- Transformers 7×1 --------------------
    st.subheader(" Transformers (TR1 – TR7)")
    for idx, tr in enumerate(power["transformers"]):
        sim = simulate_transformer(tr)
        st.markdown(
            f"""
            <div style='background:#111827; padding:14px; border-radius:10px;
                        border:1px solid #1f2937; box-shadow:0 0 10px rgba(0,0,0,0.35);
                        margin-bottom:10px;'>
                <h4 style='color:#60a5fa;'>{tr["name"]}</h4>
                <div>Status: {status_badge(tr["status"])}</div>
                <p style='color:#d1d5db; font-size:13px; margin-top:8px;'>
                    <b>Voltage:</b> {sim["voltage"]} V<br>
                    <b>Current:</b> {sim["current"]} A<br>
                    <b>Power:</b> {sim["power"]} kW<br>
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(f"Toggle {tr['name']}", key=f"tr_{idx}"):
            toggle_transformer(power, idx)
            st.rerun()

    st.markdown("---")

    # -------------------- UPS 4×1 --------------------
    st.subheader(" UPS Units (UPS1 – UPS4)")
    for idx, u in enumerate(power["ups"]):
        sim = simulate_ups(u)
        st.markdown(
            f"""
            <div style='background:#111827; padding:14px; border-radius:10px;
                        border:1px solid #1f2937; box-shadow:0 0 10px rgba(0,0,0,0.35);
                        margin-bottom:10px;'>
                <h4 style='color:#34d399;'>{u["name"]}</h4>
                <div>Status: {status_badge(u["status"])}</div>
                <p style='color:#d1d5db; font-size:13px; margin-top:8px;'>
                    <b>Voltage:</b> {sim["voltage"]} V<br>
                    <b>Current:</b> {sim["current"]} A<br>
                    <b>Power:</b> {sim["power"]} kW<br>
                    <b>Load:</b> {sim["load"]}%<br>
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(f"Toggle {u['name']}", key=f"ups_{idx}"):
            toggle_ups(power, idx)
            st.rerun()

    st.markdown("---")

    # -------------------- Gensets 7×1 --------------------
    st.subheader(" Gensets (G1 – G7)")
    for idx, g in enumerate(power["genset"]):
        sim = simulate_genset(g)
        st.markdown(
            f"""
            <div style='background:#111827; padding:14px; border-radius:10px;
                        border:1px solid #1f2937; box-shadow:0 0 10px rgba(0,0,0,0.35);
                        margin-bottom:10px;'>
                <h4 style='color:#f97316;'>{g["name"]}</h4>
                <div>Status: {status_badge(g["status"])}</div>
                <p style='color:#d1d5db; font-size:13px; margin-top:8px;'>
                    <b>Voltage:</b> {sim["voltage"]} V<br>
                    <b>Current:</b> {sim["current"]} A<br>
                    <b>Power:</b> {sim["power"]} kW<br>
                    <b>Load:</b> {sim["load"]}%<br>
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(f"Toggle {g['name']}", key=f"gen_{idx}"):
            toggle_genset(power, idx)
            st.rerun()

    st.markdown("---")

    # -------------------- PAHU 4×1 --------------------
    st.subheader(" PAHU Units (PAHU1 – PAHU4)")
    for idx, p in enumerate(power["pahu"]):
        sim = simulate_pahu(p)
        st.markdown(
            f"""
            <div style='background:#111827; padding:14px; border-radius:10px;
                        border:1px solid #1f2937; box-shadow:0 0 10px rgba(0,0,0,0.35);
                        margin-bottom:10px;'>
                <h4 style='color:#22c55e;'>{p["name"]}</h4>
                <div>Status: {status_badge(p["status"])}</div>
                <p style='color:#d1d5db; font-size:13px; margin-top:8px;'>
                    <b>Supply Air Temp:</b> {sim["supply_air_temp"]} °C<br>
                    <b>Return Air Temp:</b> {sim["return_air_temp"]} °C<br>
                    <b>Airflow:</b> {sim["airflow"]} CFM<br>
                    <b>Power:</b> {sim["power"]} kW<br>
                    <b>Filter ΔP:</b> {sim["filter_dp"]} in WG<br>
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(f"Toggle {p['name']}", key=f"pahu_{idx}"):
            toggle_pahu(power, idx)
            st.rerun()


# -------------------------------------------------------------
# VOICE ASSISTANT PAGE – FREE STT + TTS
# -------------------------------------------------------------
elif menu == "Voice Assistant":
    st.title(" Voice Assistant – Free STT + TTS (SpeechRecognition + gTTS)")

    st.write(
        "Upload a short **WAV** file with a command like "
        "`turn on chiller 5`, `set chiller 3 setpoint to 20`, "
        "`turn off transformer 2`, `turn on genset 4`, `turn off ups 1`, etc.\n\n"
        "The app will:\n"
        "1. Convert your voice to text using free Google Web Speech API (no key).\n"
        "2. Apply the BMS control rule engine.\n"
        "3. Reply back in synthetic voice using gTTS."
    )

    audio_file = st.file_uploader("Upload WAV file (16-bit PCM recommended)", type=["wav"])
    if audio_file is not None:
        raw_bytes = audio_file.read()
        with st.spinner("Transcribing with free SpeechRecognition (Google Web API)..."):
            text = transcribe_voice(raw_bytes)

        if not text:
            st.error("No speech recognized or STT error. Try again with a clearer recording.")
        else:
            st.success(f"Recognized text: **{text}**")

            # Load current configs
            chillers_data = get_chiller_data()
            power_data = get_power_data()

            # Let rule-based 'agent' handle it
            reply_text, chillers_data, power_data = voice_agent_handle_command(
                text, chillers_data, power_data
            )

            st.info(f"Agent reply: {reply_text}")

            # TTS via gTTS
            with st.spinner("Generating spoken reply with gTTS..."):
                audio_out = tts_voice(reply_text)

            st.audio(audio_out, format="audio/mp3")


# -------------------------------------------------------------
# ALARMS & EVENTS PAGE – Simulated alarms + rule-based “AI” explanation
# -------------------------------------------------------------
elif menu == "Alarms & Events":
    st.title(" Alarms & Events – BMS AI Explain")

    st.write(
        "This page simulates data center BMS alarms from chillers, transformers, "
        "UPS, gensets and environment. A simple rule-based AI explains the "
        "probable root cause and recommended operator action."
    )

    alarms = get_simulated_alarms()

    # Optional filters
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        system_filter = st.selectbox(
            "Filter by system",
            options=["All", "Chiller", "Power", "UPS", "Genset", "Environment"],
            index=0,
        )
    with col_f2:
        severity_filter = st.selectbox(
            "Filter by severity",
            options=["All", "Critical", "Major", "Minor", "Info"],
            index=0,
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

            st.markdown(
                f"""
                <div style='background:#111827; padding:14px; border-radius:10px;
                            border:1px solid #1f2937; margin-bottom:12px;'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <div>
                            <span style='color:#9ca3af; font-size:12px;'>Time</span>
                            <div style='color:#e5e7eb; font-size:13px;'>{al["timestamp"]}</div>
                        </div>
                        <div>
                            <span style='color:#9ca3af; font-size:12px;'>Severity</span><br>
                            <span style='color:{ "#f97373" if al["severity"]=="Critical" else "#facc15" if al["severity"]=="Major" else "#4ade80" if al["severity"]=="Minor" else "#60a5fa" }; font-weight:bold;'>
                                {al["severity"]}
                            </span>
                        </div>
                        <div>
                            <span style='color:#9ca3af; font-size:12px;'>System</span>
                            <div style='color:#e5e7eb; font-size:13px;'>{al["system"]}</div>
                        </div>
                        <div>
                            <span style='color:#9ca3af; font-size:12px;'>Source</span>
                            <div style='color:#e5e7eb; font-size:13px;'>{al["source"]}</div>
                        </div>
                    </div>
                    <hr style='border:1px solid #1f2937; margin-top:8px; margin-bottom:8px;'>
                    <div style='color:#e5e7eb; font-size:14px;'>
                        <b>Alarm:</b> {al["message"]}
                    </div>
                    <div style='margin-top:6px; color:#fbbf24; font-size:13px;'>
                        <b>Probable root cause:</b> {explanation["root_cause"]}
                    </div>
                    <div style='margin-top:4px; color:#93c5fd; font-size:13px;'>
                        <b>Recommended action:</b> {explanation["action"]}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
