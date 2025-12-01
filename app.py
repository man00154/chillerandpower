import streamlit as st
from chiller_manager import get_chiller_data, toggle_chiller, update_setpoint
from power_manager import (
    get_power_data, toggle_transformer, toggle_ups, toggle_genset
)
from simulator import simulate_chiller, simulate_transformer, simulate_ups, simulate_genset
from voice_agent import transcribe_google, tts_play
import base64

# -------------------------------------------------------------
# Modern Theme Page Config
# -------------------------------------------------------------
st.set_page_config(
    page_title="BMS Agent -MANISH SINGH  – Modern",
    layout="wide",
    page_icon="⚙️"
)

# -------------------------------------------------------------
# Sidebar Navigation
# -------------------------------------------------------------
menu = st.sidebar.radio(
    "📌 Navigation",
    ["Chillers", "Power Control", "Voice Assistant"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.success("Modern UI Active")

# -------------------------------------------------------------
# Helper: Status Badge
# -------------------------------------------------------------
def status_badge(status):
    color = "#16d916" if status == "ON" else "#ff4d4d"
    return f"<span style='background:{color}; padding:3px 10px; border-radius:12px; color:white; font-weight:bold;'>{status}</span>"

# -------------------------------------------------------------
# CHILLER DASHBOARD
# -------------------------------------------------------------
if menu == "Chillers":
    st.title("Chiller Dashboard – Modern UI")

    data = get_chiller_data()
    chillers = data["chillers"]

    cols_per_row = 3
    rows = len(chillers) // cols_per_row + 1

    for i in range(rows):
        row = st.columns(cols_per_row)
        for j in range(cols_per_row):
            idx = i * cols_per_row + j
            if idx >= len(chillers):
                break

            ch = chillers[idx]
            sim = simulate_chiller(ch)

            with row[j]:
                st.markdown(
                    f"""
                    <div style='background:#273346; padding:15px; border-radius:10px;'>
                        <h4 style='color:white; text-align:center;'>{ch["name"]}</h4>
                        <p>Status: {status_badge(ch["status"])}</p>
                        <hr style='border:1px solid #3a4a5b;'>
                        <p><b>Setpoint:</b> {ch["setpoint"]} °C</p>
                        <p><b>Supply Temp:</b> {sim["supply"]} °C</p>
                        <p><b>Inlet Temp:</b> {sim["inlet"]} °C</p>
                        <p><b>Outlet Temp:</b> {sim["outlet"]} °C</p>
                        <p><b>Ambient Temp:</b> {sim["ambient"]} °C</p>
                        <p><b>Comp-1:</b> {sim["comp1"]}%</p>
                        <p><b>Comp-2:</b> {sim["comp2"]}%</p>
                        <p><b>Power:</b> {sim["power"]} kW</p>
                        <p><b>Flow:</b> {sim["flow"]} m³/hr</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if st.button(f"Toggle {ch['name']}", key=f"chg_{idx}"):
                    data = toggle_chiller(data, idx)
                    st.rerun()

                new_sp = st.slider(
                    f"Setpoint {ch['name']}", 16.0, 26.0, ch["setpoint"], 0.1
                )
                if new_sp != ch["setpoint"]:
                    data = update_setpoint(data, idx, new_sp)

# -------------------------------------------------------------
# POWER CONTROL DASHBOARD
# -------------------------------------------------------------
elif menu == "Power Control":
    st.title("Power Control – Modern UI")

    power = get_power_data()

    # -------------------- Transformers --------------------
    st.header(" Transformers")

    cols = st.columns(3)
    for idx, tr in enumerate(power["transformers"]):
        sim = simulate_transformer(tr)
        with cols[idx % 3]:
            st.markdown(
                f"""
                <div style='background:#2d2d2d; padding:15px; border-radius:10px;'>
                    <h4 style='color:#4ad1ff;'>{tr["name"]}</h4>
                    Status: {status_badge(tr["status"])}<br><br>
                    <b>Voltage:</b> {sim["voltage"]} V<br>
                    <b>Current:</b> {sim["current"]} A<br>
                    <b>Power:</b> {sim["power"]} kW<br>
                </div>
                """,
                unsafe_allow_html=True
            )
            if st.button(f"Toggle {tr['name']}", key=f"tr_{idx}"):
                toggle_transformer(power, idx)
                st.rerun()

    st.markdown("---")

    # -------------------- UPS --------------------
    st.header("UPS Units")

    cols = st.columns(3)
    for idx, u in enumerate(power["ups"]):
        sim = simulate_ups(u)
        with cols[idx % 3]:
            st.markdown(
                f"""
                <div style='background:#2d2d2d; padding:15px; border-radius:10px;'>
                    <h4 style='color:#7aff7a;'>{u["name"]}</h4>
                    Status: {status_badge(u["status"])}<br><br>
                    <b>Voltage:</b> {sim["voltage"]} V<br>
                    <b>Current:</b> {sim["current"]} A<br>
                    <b>Power:</b> {sim["power"]} kW<br>
                    <b>Load:</b> {sim["load"]}%<br>
                </div>
                """,
                unsafe_allow_html=True
            )
            if st.button(f"Toggle UPS {u['name']}", key=f"ups_{idx}"):
                toggle_ups(power, idx)
                st.rerun()

    st.markdown("---")

    # -------------------- Gensets --------------------
    st.header(" Gensets")

    cols = st.columns(3)
    for idx, g in enumerate(power["genset"]):
        sim = simulate_genset(g)
        with cols[idx % 3]:
            st.markdown(
                f"""
                <div style='background:#2d2d2d; padding:15px; border-radius:10px;'>
                    <h4 style='color:#ffaa4a;'>{g["name"]}</h4>
                    Status: {status_badge(g["status"])}<br><br>
                    <b>Voltage:</b> {sim["voltage"]} V<br>
                    <b>Current:</b> {sim["current"]} A<br>
                    <b>Power:</b> {sim["power"]} kW<br>
                    <b>Load:</b> {sim["load"]}%<br>
                </div>
                """,
                unsafe_allow_html=True
            )
            if st.button(f"Toggle {g['name']}", key=f"gen_{idx}"):
                toggle_genset(power, idx)
                st.rerun()

# -------------------------------------------------------------
# VOICE ASSISTANT
# -------------------------------------------------------------
elif menu == "Voice Assistant":
    st.title(" Voice Assistant – Google Cloud STT")

    file = st.file_uploader("Upload WAV audio", type=["wav"])
    if file:
        audio_bytes = file.read()
        with st.spinner("Transcribing..."):
            text = transcribe_google(audio_bytes)
        st.success(f"You said: **{text}**")

        # TTS reply
        reply_audio = tts_play(text)
        st.audio(reply_audio, format="audio/wav")

