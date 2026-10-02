import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests

st.set_page_config(page_title="Patient Vital Monitoring System", page_icon="❤️", layout="wide")
st.title("❤️ Multi-Parameter Patient Vital Monitoring System")
st.write("Multi-parameter physiological monitoring and early warning framework with manual input and simulation modes.")
st.divider()

# Original research-model thresholds
TEMP_MIN, TEMP_MAX = 36.1, 37.5
HR_MIN, HR_MAX = 60, 100
SPO2_MIN = 95
SYS_BP_MIN, SYS_BP_MAX = 90, 129
DIA_BP_MIN, DIA_BP_MAX = 60, 84
RR_MIN, RR_MAX = 12, 20

W_TEMP, W_HR, W_SPO2, W_BP, W_RR = 0.15, 0.20, 0.30, 0.20, 0.15

def temperature_score(v):
    if TEMP_MIN <= v <= TEMP_MAX: return 0.0
    if 37.5 < v <= 38.0: return 0.3
    if 38.0 < v <= 39.0: return 0.6
    if v > 39.0: return 1.0
    return 0.6

def heart_rate_score(v):
    if HR_MIN <= v <= HR_MAX: return 0.0
    if 100 < v <= 110: return 0.3
    if 110 < v <= 130: return 0.6
    if v > 130: return 1.0
    return 0.6

def spo2_score(v):
    if v >= 95: return 0.0
    if 93 <= v < 95: return 0.3
    if 90 <= v < 93: return 0.6
    return 1.0

def blood_pressure_score(s, d):
    if SYS_BP_MIN <= s <= SYS_BP_MAX and DIA_BP_MIN <= d <= DIA_BP_MAX: return 0.0
    score = 0.0
    if s > SYS_BP_MAX or d > DIA_BP_MAX: score = 0.3
    if s > 150 or d > 95: score = 0.6
    if s > 180 or d > 120: score = 1.0
    if s < SYS_BP_MIN or d < DIA_BP_MIN: score = max(score, 0.3)
    return min(score, 1.0)

def respiratory_score(v):
    if RR_MIN <= v <= RR_MAX: return 0.0
    if 20 < v <= 25: return 0.3
    if 25 < v <= 30: return 0.6
    if v > 30: return 1.0
    return 0.6

def calculate_risk(temp, hr, spo2, s, d, rr):
    return (W_TEMP * temperature_score(temp) + W_HR * heart_rate_score(hr) +
            W_SPO2 * spo2_score(spo2) + W_BP * blood_pressure_score(s, d) +
            W_RR * respiratory_score(rr))

def classify_status(risk):
    if risk < 0.15: return "NORMAL"
    if risk < 0.40: return "WARNING"
    return "CRITICAL"

# Real-world reference interpretation for adult resting measurements
def temp_interpret(v):
    if v < 97.7: return "LOW", "Low Temperature"
    if v < 99.2: return "NORMAL", "Normal Temperature"
    if v < 100.4: return "HIGH", "Slightly High Temperature"
    return "HIGH", "High Temperature / Fever"

def hr_interpret(v):
    if v < 60: return "LOW", "Low Heart Rate"
    if v <= 100: return "NORMAL", "Normal Heart Rate"
    return "HIGH", "High Heart Rate"

def spo2_interpret(v):
    if v >= 95: return "NORMAL", "Normal Oxygen Level"
    return "LOW", "Low Oxygen Level"

def bp_interpret(s, d):
    if s <= 90 or d <= 60: return "LOW", "Low Blood Pressure"
    if s < 120 and d < 80: return "NORMAL", "Normal Blood Pressure"
    if 120 <= s <= 129 and d < 80: return "HIGH", "Elevated Blood Pressure"
    return "HIGH", "High Blood Pressure"

def rr_interpret(v):
    if v < 12: return "LOW", "Low Respiratory Rate"
    if v <= 18: return "NORMAL", "Normal Respiratory Rate"
    return "HIGH", "High / Elevated Respiratory Rate"

def interpretations(tf, hr, spo2, s, d, rr):
    return {
        "Temperature": temp_interpret(tf),
        "Heart Rate": hr_interpret(hr),
        "SpO₂": spo2_interpret(spo2),
        "Blood Pressure": bp_interpret(s, d),
        "Respiratory Rate": rr_interpret(rr)
    }

def abnormal_conditions(x):
    return [f"{k}: {v[1]}" for k, v in x.items() if v[0] != "NORMAL"]

def send_telegram_message(message):
    try:
        token = st.secrets["TELEGRAM_BOT_TOKEN"]
        chat_id = st.secrets["TELEGRAM_CHAT_ID"]
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={"chat_id": chat_id, "text": message}, timeout=10
        )
        return r.ok
    except Exception:
        return False

def send_alert(patient_id, mode, status, risk, tf, hr, spo2, s, d, rr, info):
    if status == "NORMAL": return False
    title = "🟡 PATIENT STATUS ALERT" if status == "WARNING" else "🔴 CRITICAL PATIENT ALERT"
    conditions = abnormal_conditions(info)
    msg = (
        f"{title}\n\nPatient ID: {patient_id}\nStatus: {status}\nMode: {mode}\n"
        f"Risk Score: {risk:.2f}\n\nTemperature: {tf:.1f} °F\n"
        f"Heart Rate: {hr:.0f} BPM\nSpO₂: {spo2:.0f}%\n"
        f"Blood Pressure: {s:.0f}/{d:.0f} mmHg\nRespiratory Rate: {rr:.0f}/min\n\n"
        "Parameter Interpretation:\n"
        f"• Temperature: {info['Temperature'][1]}\n"
        f"• Heart Rate: {info['Heart Rate'][1]}\n"
        f"• SpO₂: {info['SpO₂'][1]}\n"
        f"• Blood Pressure: {info['Blood Pressure'][1]}\n"
        f"• Respiratory Rate: {info['Respiratory Rate'][1]}\n"
    )
    if conditions:
        msg += "\nDetected Conditions:\n" + "\n".join("• " + x for x in conditions)
    return send_telegram_message(msg)

# ============================================================
# MODE
# ============================================================
st.sidebar.header("⚙️ Monitoring Settings")
mode = st.sidebar.radio("Monitoring Mode", ["Manual Patient Input", "Simulation"])
patient_id = st.sidebar.text_input("Patient ID", "P001")

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests

st.set_page_config(page_title="Patient Vital Monitoring System", page_icon="❤️", layout="wide")
st.title("❤️ Multi-Parameter Patient Vital Monitoring System")
st.write("Multi-parameter physiological monitoring and early warning framework with manual input and simulation modes.")
st.divider()

# Original research-model thresholds
TEMP_MIN, TEMP_MAX = 36.1, 37.5
HR_MIN, HR_MAX = 60, 100
SPO2_MIN = 95
SYS_BP_MIN, SYS_BP_MAX = 90, 129
DIA_BP_MIN, DIA_BP_MAX = 60, 84
RR_MIN, RR_MAX = 12, 20

W_TEMP, W_HR, W_SPO2, W_BP, W_RR = 0.15, 0.20, 0.30, 0.20, 0.15

def temperature_score(v):
    if TEMP_MIN <= v <= TEMP_MAX: return 0.0
    if 37.5 < v <= 38.0: return 0.3
    if 38.0 < v <= 39.0: return 0.6
    if v > 39.0: return 1.0
    return 0.6

def heart_rate_score(v):
    if HR_MIN <= v <= HR_MAX: return 0.0
    if 100 < v <= 110: return 0.3
    if 110 < v <= 130: return 0.6
    if v > 130: return 1.0
    return 0.6

def spo2_score(v):
    if v >= 95: return 0.0
    if 93 <= v < 95: return 0.3
    if 90 <= v < 93: return 0.6
    return 1.0

def blood_pressure_score(s, d):
    if SYS_BP_MIN <= s <= SYS_BP_MAX and DIA_BP_MIN <= d <= DIA_BP_MAX: return 0.0
    score = 0.0
    if s > SYS_BP_MAX or d > DIA_BP_MAX: score = 0.3
    if s > 150 or d > 95: score = 0.6
    if s > 180 or d > 120: score = 1.0
    if s < SYS_BP_MIN or d < DIA_BP_MIN: score = max(score, 0.3)
    return min(score, 1.0)

def respiratory_score(v):
    if RR_MIN <= v <= RR_MAX: return 0.0
    if 20 < v <= 25: return 0.3
    if 25 < v <= 30: return 0.6
    if v > 30: return 1.0
    return 0.6

def calculate_risk(temp, hr, spo2, s, d, rr):
    return (W_TEMP * temperature_score(temp) + W_HR * heart_rate_score(hr) +
            W_SPO2 * spo2_score(spo2) + W_BP * blood_pressure_score(s, d) +
            W_RR * respiratory_score(rr))

def classify_status(risk):
    if risk < 0.15: return "NORMAL"
    if risk < 0.40: return "WARNING"
    return "CRITICAL"

# Real-world reference interpretation for adult resting measurements
def temp_interpret(v):
    if v < 97.7: return "LOW", "Low Temperature"
    if v < 99.2: return "NORMAL", "Normal Temperature"
    if v < 100.4: return "HIGH", "Slightly High Temperature"
    return "HIGH", "High Temperature / Fever"

def hr_interpret(v):
    if v < 60: return "LOW", "Low Heart Rate"
    if v <= 100: return "NORMAL", "Normal Heart Rate"
    return "HIGH", "High Heart Rate"

def spo2_interpret(v):
    if v >= 95: return "NORMAL", "Normal Oxygen Level"
    return "LOW", "Low Oxygen Level"

def bp_interpret(s, d):
    if s <= 90 or d <= 60: return "LOW", "Low Blood Pressure"
    if s < 120 and d < 80: return "NORMAL", "Normal Blood Pressure"
    if 120 <= s <= 129 and d < 80: return "HIGH", "Elevated Blood Pressure"
    return "HIGH", "High Blood Pressure"

def rr_interpret(v):
    if v < 12: return "LOW", "Low Respiratory Rate"
    if v <= 18: return "NORMAL", "Normal Respiratory Rate"
    return "HIGH", "High / Elevated Respiratory Rate"

def interpretations(tf, hr, spo2, s, d, rr):
    return {
        "Temperature": temp_interpret(tf),
        "Heart Rate": hr_interpret(hr),
        "SpO₂": spo2_interpret(spo2),
        "Blood Pressure": bp_interpret(s, d),
        "Respiratory Rate": rr_interpret(rr)
    }

def abnormal_conditions(x):
    return [f"{k}: {v[1]}" for k, v in x.items() if v[0] != "NORMAL"]

def send_telegram_message(message):
    try:
        token = st.secrets["TELEGRAM_BOT_TOKEN"]
        chat_id = st.secrets["TELEGRAM_CHAT_ID"]
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={"chat_id": chat_id, "text": message}, timeout=10
        )
        return r.ok
    except Exception:
        return False

def send_alert(patient_id, mode, status, risk, tf, hr, spo2, s, d, rr, info):
    if status == "NORMAL": return False
    title = "🟡 PATIENT STATUS ALERT" if status == "WARNING" else "🔴 CRITICAL PATIENT ALERT"
    conditions = abnormal_conditions(info)
    msg = (
        f"{title}\n\nPatient ID: {patient_id}\nStatus: {status}\nMode: {mode}\n"
        f"Risk Score: {risk:.2f}\n\nTemperature: {tf:.1f} °F\n"
        f"Heart Rate: {hr:.0f} BPM\nSpO₂: {spo2:.0f}%\n"
        f"Blood Pressure: {s:.0f}/{d:.0f} mmHg\nRespiratory Rate: {rr:.0f}/min\n\n"
        "Parameter Interpretation:\n"
        f"• Temperature: {info['Temperature'][1]}\n"
        f"• Heart Rate: {info['Heart Rate'][1]}\n"
        f"• SpO₂: {info['SpO₂'][1]}\n"
        f"• Blood Pressure: {info['Blood Pressure'][1]}\n"
        f"• Respiratory Rate: {info['Respiratory Rate'][1]}\n"
    )
    if conditions:
        msg += "\nDetected Conditions:\n" + "\n".join("• " + x for x in conditions)
    return send_telegram_message(msg)

# ============================================================
# MODE
# ============================================================
st.sidebar.header("⚙️ Monitoring Settings")
mode = st.sidebar.radio("Monitoring Mode", ["Manual Patient Input", "Simulation"])
patient_id = st.sidebar.text_input("Patient ID", "P001")

if mode == "Manual Patient Input":
    st.subheader("🧑‍⚕️ Manual Patient Vital Input")
    st.info("Enter measured values. Analysis, risk score and status update automatically; no Analyze button is required.")

    c1, c2, c3 = st.columns(3)
    with c1:
        tf = st.number_input("🌡 Body Temperature (°F)", 85.0, 110.0, 98.6, 0.1)
    with c2:
        hr = st.number_input("❤️ Heart Rate (BPM)", 20, 220, 75, 1)
    with c3:
        spo2 = st.number_input("🫁 SpO₂ (%)", 50, 100, 98, 1)

    c4, c5, c6 = st.columns(3)
    with c4:
        s = st.number_input("🩸 Systolic BP (mmHg)", 40, 250, 120, 1)
    with c5:
        d = st.number_input("🩸 Diastolic BP (mmHg)", 20, 160, 80, 1)
    with c6:
        rr = st.number_input("🌬 Respiratory Rate (/min)", 4, 60, 16, 1)

    tc = (tf - 32) * 5 / 9
    info = interpretations(tf, hr, spo2, s, d, rr)
    risk = calculate_risk(tc, hr, spo2, s, d, rr)
    status = classify_status(risk)

    # ============================================================
    # SAVE CURRENT MEASUREMENT TO PATIENT HISTORY
    # ============================================================

    from datetime import datetime

    current_measurement = {
        "Time": datetime.now().strftime("%H:%M:%S"),
        "Temperature (°F)": tf,
        "Temperature (°C)": tc,
        "Heart Rate (BPM)": hr,
        "SpO₂ (%)": spo2,
        "Systolic BP": s,
        "Diastolic BP": d,
        "Respiratory Rate": rr,
        "Risk Score": risk,
        "Status": status
    }

    # Save only when the measurement is different
    history = st.session_state.patient_history[patient_id]

    if not history or history[-1] != current_measurement:
        history.append(current_measurement)
        
            # ============================================================
    # DISPLAY PATIENT MONITORING HISTORY
    # ============================================================

    history_data = pd.DataFrame(
        st.session_state.patient_history[patient_id]
    )

    st.divider()

    st.subheader("🕒 Patient Monitoring History")

    if not history_data.empty:
        st.dataframe(
            history_data,
            use_container_width=True,
            hide_index=True
        )

    # ============================================================
    # CURRENT PATIENT STATUS
    # ============================================================

    st.subheader("📌 Current Patient Status")

    if status == "NORMAL":
        st.success("🟢 Current Status: NORMAL")

    elif status == "WARNING":
        st.warning("🟡 Current Status: WARNING")

    else:
        st.error("🔴 Current Status: CRITICAL")

    st.caption(
        f"Patient {patient_id} | "
        f"Total Measurements: {len(history_data)}"
    )
    
        # ============================================================
    # PATIENT MONITORING GRAPHS
    # ============================================================

    st.divider()
    st.subheader("📈 Patient Monitoring Graphs")

    if len(history_data) >= 2:

        # --------------------------------------------------------
        # Temperature Graph
        # --------------------------------------------------------

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=history_data["Time"],
                y=history_data["Temperature (°F)"],
                mode="lines+markers",
                name="Temperature"
            )
        )

        fig.update_layout(
            title="🌡 Temperature Trend",
            xaxis_title="Time",
            yaxis_title="Temperature (°F)",
            height=350
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # --------------------------------------------------------
        # Heart Rate Graph
        # --------------------------------------------------------

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=history_data["Time"],
                y=history_data["Heart Rate (BPM)"],
                mode="lines+markers",
                name="Heart Rate"
            )
        )

        fig.update_layout(
            title="❤️ Heart Rate Trend",
            xaxis_title="Time",
            yaxis_title="Heart Rate (BPM)",
            height=350
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # --------------------------------------------------------
        # SpO₂ Graph
        # --------------------------------------------------------

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=history_data["Time"],
                y=history_data["SpO₂ (%)"],
                mode="lines+markers",
                name="SpO₂"
            )
        )

        fig.update_layout(
            title="🫁 SpO₂ Trend",
            xaxis_title="Time",
            yaxis_title="SpO₂ (%)",
            height=350
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # --------------------------------------------------------
        # Blood Pressure Graph
        # --------------------------------------------------------

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=history_data["Time"],
                y=history_data["Systolic BP"],
                mode="lines+markers",
                name="Systolic BP"
            )
        )

        fig.add_trace(
            go.Scatter(
                x=history_data["Time"],
                y=history_data["Diastolic BP"],
                mode="lines+markers",
                name="Diastolic BP"
            )
        )

        fig.update_layout(
            title="🩸 Blood Pressure Trend",
            xaxis_title="Time",
            yaxis_title="Blood Pressure (mmHg)",
            height=350
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # --------------------------------------------------------
        # Respiratory Rate Graph
        # --------------------------------------------------------

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=history_data["Time"],
                y=history_data["Respiratory Rate"],
                mode="lines+markers",
                name="Respiratory Rate"
            )
        )

        fig.update_layout(
            title="🌬 Respiratory Rate Trend",
            xaxis_title="Time",
            yaxis_title="Respiratory Rate (/min)",
            height=350
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # --------------------------------------------------------
        # Risk Score Graph
        # --------------------------------------------------------

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=history_data["Time"],
                y=history_data["Risk Score"],
                mode="lines+markers",
                name="Risk Score"
            )
        )

        fig.add_hline(
            y=0.15,
            line_dash="dash",
            annotation_text="Warning Threshold"
        )

        fig.add_hline(
            y=0.40,
            line_dash="dash",
            annotation_text="Critical Threshold"
        )

        fig.update_layout(
            title="🧠 Patient Risk Score Trend",
            xaxis_title="Time",
            yaxis_title="Risk Score",
            yaxis_range=[0, 1],
            height=400
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:

        st.info(
            "📊 At least 2 measurements are required "
            "to display patient monitoring graphs."
        )
        
            # ============================================================
    # PATIENT STATUS EVENT HISTORY
    # ============================================================

    st.divider()
    st.subheader("🚨 Patient Status Event History")

    if not history_data.empty:

        # Find measurements where patient was not NORMAL
        abnormal_history = history_data[
            history_data["Status"] != "NORMAL"
        ]

        if not abnormal_history.empty:

            st.warning(
                f"⚠️ {len(abnormal_history)} abnormal measurement(s) "
                "recorded for this patient."
            )

            event_columns = [
                "Time",
                "Status",
                "Risk Score",
                "Temperature (°F)",
                "Heart Rate (BPM)",
                "SpO₂ (%)",
                "Systolic BP",
                "Diastolic BP",
                "Respiratory Rate"
            ]

            st.dataframe(
                abnormal_history[event_columns],
                use_container_width=True,
                hide_index=True
            )

        else:

            st.success(
                "🟢 No abnormal event has been recorded "
                "for this patient."
            )

    # ============================================================
    # MONITORING SUMMARY
    # ============================================================

    st.subheader("📋 Monitoring Summary")

    total_measurements = len(history_data)

    warning_count = int(
        (history_data["Status"] == "WARNING").sum()
    )

    critical_count = int(
        (history_data["Status"] == "CRITICAL").sum()
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Total Measurements",
            total_measurements
        )

    with col2:
        st.metric(
            "Warning Events",
            warning_count
        )

    with col3:
        st.metric(
            "Critical Events",
            critical_count
        )
        
            # ============================================================
    # CURRENT CONDITION & TREND SUMMARY
    # ============================================================

    st.divider()
    st.subheader("🩺 Current Condition & Trend Summary")

    # ------------------------------------------------------------
    # Current Status
    # ------------------------------------------------------------

    if status == "NORMAL":
        current_condition = "NORMAL"
    elif status == "WARNING":
        current_condition = "WARNING"
    else:
        current_condition = "CRITICAL"

    # ------------------------------------------------------------
    # Recent Status Trend
    # ------------------------------------------------------------

    recent_statuses = history_data["Status"].tail(3).tolist()

    if len(recent_statuses) >= 2:

        if recent_statuses[-1] == "NORMAL" and recent_statuses[-2] != "NORMAL":
            condition_trend = "IMPROVING"

        elif recent_statuses[-1] != "NORMAL" and recent_statuses[-2] == "NORMAL":
            condition_trend = "DETERIORATING"

        elif recent_statuses[-1] == recent_statuses[-2]:
            condition_trend = "STABLE"

        else:
            condition_trend = "CHANGING"

    else:
        condition_trend = "INSUFFICIENT DATA"

    # ------------------------------------------------------------
    # Previous Abnormal Event
    # ------------------------------------------------------------

    abnormal_history = history_data[
        history_data["Status"] != "NORMAL"
    ]

    if not abnormal_history.empty:

        last_abnormal = abnormal_history.iloc[-1]

        previous_event_text = (
            f"{last_abnormal['Status']} at "
            f"{last_abnormal['Time']}"
        )

    else:

        previous_event_text = "No previous abnormal event"

    # ------------------------------------------------------------
    # Display Summary
    # ------------------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:

        if current_condition == "NORMAL":
            st.success("🟢 Current Status\n\nNORMAL")

        elif current_condition == "WARNING":
            st.warning("🟡 Current Status\n\nWARNING")

        else:
            st.error("🔴 Current Status\n\nCRITICAL")

    with col2:

        if condition_trend == "IMPROVING":
            st.success("📈 Recent Trend\n\nIMPROVING")

        elif condition_trend == "DETERIORATING":
            st.error("📉 Recent Trend\n\nDETERIORATING")

        elif condition_trend == "STABLE":
            st.info("➡️ Recent Trend\n\nSTABLE")

        else:
            st.info(
                f"🔄 Recent Trend\n\n{condition_trend}"
            )

    with col3:

        st.info(
            f"🚨 Previous Event\n\n"
            f"{previous_event_text}"
        )

    # ------------------------------------------------------------
    # Doctor-oriented summary message
    # ------------------------------------------------------------

    if current_condition == "NORMAL":

        if condition_trend == "IMPROVING":
            st.success(
                "🟢 The patient's current status is NORMAL "
                "and the recent condition is improving."
            )

        elif abnormal_history.empty:
            st.success(
                "🟢 The patient has remained NORMAL "
                "during the recorded monitoring period."
            )

        else:
            st.info(
                "🟢 The patient is currently NORMAL, "
                "but previous abnormal events remain recorded "
                "in the monitoring history."
            )

    elif current_condition == "WARNING":

        st.warning(
            "🟡 The patient is currently in WARNING status. "
            "Continued monitoring is recommended."
        )

    else:

        st.error(
            "🔴 The patient is currently in CRITICAL status. "
            "The abnormal condition is currently active."
        )
    st.divider()
    st.subheader("📊 Patient Vital Analysis")

    rows = [
        ("🌡 Temperature", f"{tf:.1f} °F", info["Temperature"]),
        ("❤️ Heart Rate", f"{hr:.0f} BPM", info["Heart Rate"]),
        ("🫁 SpO₂", f"{spo2:.0f} %", info["SpO₂"]),
        ("🩸 Blood Pressure", f"{s:.0f}/{d:.0f} mmHg", info["Blood Pressure"]),
        ("🌬 Respiratory Rate", f"{rr:.0f} /min", info["Respiratory Rate"])
    ]
    for name, value, result in rows:
        a, b, c = st.columns([2, 1.5, 3])
        icon = "🟢" if result[0] == "NORMAL" else ("🔴" if result[0] == "HIGH" else "🔵")
        with a: st.write(f"**{name}**")
        with b: st.write(f"**{value}**")
        with c: st.write(f"{icon} **{result[1]}**")

    st.divider()
    a, b = st.columns(2)
    with a: st.metric("Overall Status", status)
    with b: st.metric("Risk Score", f"{risk:.2f}")

    if status == "NORMAL":
        st.success("🟢 NORMAL — All monitored parameters are within the model's normal risk range.")
    elif status == "WARNING":
        st.warning("🟡 WARNING — One or more parameters contribute to an elevated model risk level.")
    else:
        st.error("🔴 CRITICAL — The combined model risk has reached the critical threshold.")

    conditions = abnormal_conditions(info)
    st.subheader("🚨 Detected Conditions")
    if conditions:
        for x in conditions: st.write("• " + x)
    else:
        st.success("No parameter-specific abnormal interpretation detected.")

    # Deduplication prevents Telegram spam on Streamlit reruns.
    key = f"{patient_id}|{tf:.1f}|{hr}|{spo2}|{s}|{d}|{rr}|{status}"
    if "manual_alerts" not in st.session_state:
        st.session_state.manual_alerts = set()
    if status in ("WARNING", "CRITICAL") and key not in st.session_state.manual_alerts:
        if send_alert(patient_id, "Manual Patient Input", status, risk, tf, hr, spo2, s, d, rr, info):
            st.session_state.manual_alerts.add(key)
            st.toast("Telegram alert sent successfully.", icon="📲")

    st.divider()
    st.caption("Reference interpretations are for this research prototype and are not a clinical diagnosis. Interpretation varies with age, measurement method, activity and clinical context.")

else:
    # ========================================================
    # SIMULATION
    # ========================================================
    st.sidebar.subheader("Simulation Scenario")
    scenario = st.sidebar.selectbox("Select Patient Scenario", [
        "Normal Patient", "Fever Progression",
        "Respiratory Deterioration", "Multi-Parameter Deterioration"
    ])

    duration = 60
    time = np.arange(duration)

    if scenario == "Normal Patient":
        temperature, heart_rate, spo2 = np.full(duration,36.8), np.full(duration,76), np.full(duration,98)
        systolic_bp, diastolic_bp, respiratory_rate = np.full(duration,120), np.full(duration,80), np.full(duration,16)
    elif scenario == "Fever Progression":
        temperature = np.r_[np.linspace(36.8,39.5,30), np.linspace(39.5,38.0,30)]
        heart_rate = np.r_[np.linspace(76,125,30), np.linspace(125,90,30)]
        spo2 = np.full(duration,97)
        systolic_bp, diastolic_bp = np.full(duration,125), np.full(duration,82)
        respiratory_rate = np.r_[np.linspace(16,26,30), np.linspace(26,18,30)]
    elif scenario == "Respiratory Deterioration":
        temperature = np.full(duration,37.1)
        heart_rate = np.r_[np.linspace(78,115,30), np.linspace(115,95,30)]
        spo2 = np.r_[np.linspace(98,87,30), np.linspace(87,96,30)]
        systolic_bp, diastolic_bp = np.full(duration,120), np.full(duration,80)
        respiratory_rate = np.r_[np.linspace(16,32,30), np.linspace(32,18,30)]
    else:
        temperature = np.r_[np.linspace(36.8,39.5,30), np.linspace(39.5,37.2,30)]
        heart_rate = np.r_[np.linspace(76,135,30), np.linspace(135,85,30)]
        spo2 = np.r_[np.linspace(98,86,30), np.linspace(86,97,30)]
        systolic_bp = np.r_[np.linspace(120,165,30), np.linspace(165,125,30)]
        diastolic_bp = np.r_[np.linspace(80,100,30), np.linspace(100,82,30)]
        respiratory_rate = np.r_[np.linspace(16,32,30), np.linspace(32,18,30)]

    temperature, heart_rate, spo2 = np.round(temperature,2), np.round(heart_rate,1), np.round(spo2,1)
    systolic_bp, diastolic_bp, respiratory_rate = np.round(systolic_bp,1), np.round(diastolic_bp,1), np.round(respiratory_rate,1)

    risks = np.array([calculate_risk(temperature[i],heart_rate[i],spo2[i],systolic_bp[i],diastolic_bp[i],respiratory_rate[i]) for i in range(duration)])
    statuses = np.array([classify_status(x) for x in risks])

    data = pd.DataFrame({
        "Time (min)":time, "Temperature (°C)":temperature,
        "Heart Rate (BPM)":heart_rate, "SpO₂ (%)":spo2,
        "Systolic BP":systolic_bp, "Diastolic BP":diastolic_bp,
        "Respiratory Rate":respiratory_rate, "Risk Score":risks, "Status":statuses
    })

    idx = np.where(data["Status"] != "NORMAL")[0]
    if len(idx):
        i = int(idx[0])
        alert_tf = float(data["Temperature (°C)"].iloc[i])*9/5+32
        info = interpretations(alert_tf,float(data["Heart Rate (BPM)"].iloc[i]),float(data["SpO₂ (%)"].iloc[i]),float(data["Systolic BP"].iloc[i]),float(data["Diastolic BP"].iloc[i]),float(data["Respiratory Rate"].iloc[i]))
        key = f"{scenario}_{statuses[i]}_{i}"
        if "simulation_alerts" not in st.session_state: st.session_state.simulation_alerts = set()
        if key not in st.session_state.simulation_alerts:
            if send_alert(patient_id, scenario, statuses[i], float(risks[i]), alert_tf, float(data["Heart Rate (BPM)"].iloc[i]), float(data["SpO₂ (%)"].iloc[i]), float(data["Systolic BP"].iloc[i]), float(data["Diastolic BP"].iloc[i]), float(data["Respiratory Rate"].iloc[i]), info):
                st.session_state.simulation_alerts.add(key)

    # Model comparison
    st.divider()
    st.subheader("🔬 Model Comparison")
    temp_scores = np.array([temperature_score(x) for x in data["Temperature (°C)"]])
    temp_status = np.array([classify_status(x) for x in temp_scores])
    mi = np.where(statuses != "NORMAL")[0]
    ti = np.where(temp_status != "NORMAL")[0]
    comparison = pd.DataFrame({
        "Metric":["Detection Model","First Detection Time","Abnormal Time Points","Peak Risk Score"],
        "Temperature-Only Model":["Temperature only",f"{time[ti[0]]} min" if len(ti) else "Not detected",int(np.sum(temp_status!="NORMAL")),f"{temp_scores.max():.2f}"],
        "Multi-Parameter Model":["5 physiological parameters",f"{time[mi[0]]} min" if len(mi) else "Not detected",int(np.sum(statuses!="NORMAL")),f"{risks.max():.2f}"]
    })
    st.dataframe(comparison,use_container_width=True,hide_index=True)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=time,y=temp_scores,mode="lines",name="Temperature-Only Model"))
    fig.add_trace(go.Scatter(x=time,y=risks,mode="lines",name="Multi-Parameter Model"))
    fig.add_hline(y=0.15,line_dash="dash",annotation_text="Warning Threshold")
    fig.add_hline(y=0.40,line_dash="dash",annotation_text="Critical Threshold")
    fig.update_layout(title="Temperature-Only vs Multi-Parameter Risk Detection",xaxis_title="Time (minutes)",yaxis_title="Risk / Severity Score",yaxis_range=[0,1],height=500)
    st.plotly_chart(fig,use_container_width=True)

    # Patient information and latched status
    st.subheader("👤 Patient Information")
    a,b,c = st.columns(3)
    with a: st.write(f"**Patient ID:** {patient_id}")
    with b: st.write("**Monitoring Mode:** Simulation")
    with c: st.write(f"**Scenario:** {scenario}")

    latest = data.iloc[-1]
    latest_tf = float(latest["Temperature (°C)"])*9/5+32
    st.divider()
    st.subheader("📊 Current Vital Signs")
    a,b,c = st.columns(3)
    with a: st.metric("🌡 Temperature",f"{latest_tf:.1f} °F")
    with b: st.metric("❤️ Heart Rate",f"{latest['Heart Rate (BPM)']:.0f} BPM")
    with c: st.metric("🫁 SpO₂",f"{latest['SpO₂ (%)']:.0f} %")
    a,b = st.columns(2)
    with a: st.metric("🩸 Blood Pressure",f"{latest['Systolic BP']:.0f}/{latest['Diastolic BP']:.0f} mmHg")
    with b: st.metric("🌬 Respiratory Rate",f"{latest['Respiratory Rate']:.0f} /min")

    st.divider()
    st.subheader("🧠 Risk Assessment")
    a,b,c = st.columns(3)
    with a: st.metric("Current Risk Score",f"{latest['Risk Score']:.2f}")
    with b: st.metric("Peak Risk Score",f"{risks.max():.2f}")
    with c: st.metric("Critical Time Points",f"{np.sum(statuses=='CRITICAL')} min")

    website_status = "CRITICAL" if "CRITICAL" in statuses else ("WARNING" if "WARNING" in statuses else "NORMAL")
    if website_status == "NORMAL": st.success("🟢 NORMAL — No warning or critical event was detected during the simulation.")
    elif website_status == "WARNING": st.warning("🟡 WARNING — The simulated patient reached an elevated risk level during the monitoring period.")
    else: st.error("🔴 CRITICAL — The simulated patient reached a high risk level during the monitoring period.")

    if website_status != "NORMAL":
        first = int(np.where(statuses!="NORMAL")[0][0])
        st.caption(f"🚨 {website_status} event detected at {time[first]} min | Peak Risk Score: {risks.max():.2f}")
        if latest["Status"] == "NORMAL":
            st.info("The simulated parameters returned toward normal during recovery. The abnormal event remains displayed above.")

    # Graphs
    st.divider()
    st.subheader("📈 Risk Score vs Time")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=time,y=risks,mode="lines+markers",name="Risk Score"))
    fig.add_hline(y=0.15,line_dash="dash",annotation_text="Warning Threshold")
    fig.add_hline(y=0.40,line_dash="dash",annotation_text="Critical Threshold")
    fig.update_layout(xaxis_title="Time (minutes)",yaxis_title="Risk Score",yaxis_range=[0,1],height=450)
    st.plotly_chart(fig,use_container_width=True)

    st.subheader("📊 Vital Sign Trends")
    for col, title, ylabel in [
        ("Temperature (°C)","Temperature Trend","Temperature (°C)"),
        ("Heart Rate (BPM)","Heart Rate Trend","Heart Rate (BPM)"),
        ("SpO₂ (%)","SpO₂ Trend","SpO₂ (%)"),
        ("Respiratory Rate","Respiratory Rate Trend","Respiratory Rate (/min)")
    ]:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=time,y=data[col],mode="lines",name=title))
        fig.update_layout(title=title,xaxis_title="Time (minutes)",yaxis_title=ylabel,height=400)
        st.plotly_chart(fig,use_container_width=True)

    st.subheader("📋 Simulation Dataset")
    st.dataframe(data,use_container_width=True)

    st.caption("This simulation uses predefined physiological ranges, weights and risk thresholds for research experimentation. It is not intended for clinical diagnosis.")
if mode == "Manual Patient Input":
    st.subheader("🧑‍⚕️ Manual Patient Vital Input")
    st.info("Enter measured values. Analysis, risk score and status update automatically; no Analyze button is required.")

    c1, c2, c3 = st.columns(3)
    with c1:
        tf = st.number_input("🌡 Body Temperature (°F)", 85.0, 110.0, 98.6, 0.1)
    with c2:
        hr = st.number_input("❤️ Heart Rate (BPM)", 20, 220, 75, 1)
    with c3:
        spo2 = st.number_input("🫁 SpO₂ (%)", 50, 100, 98, 1)

    c4, c5, c6 = st.columns(3)
    with c4:
        s = st.number_input("🩸 Systolic BP (mmHg)", 40, 250, 120, 1)
    with c5:
        d = st.number_input("🩸 Diastolic BP (mmHg)", 20, 160, 80, 1)
    with c6:
        rr = st.number_input("🌬 Respiratory Rate (/min)", 4, 60, 16, 1)

    tc = (tf - 32) * 5 / 9
    info = interpretations(tf, hr, spo2, s, d, rr)
    risk = calculate_risk(tc, hr, spo2, s, d, rr)
    status = classify_status(risk)

    st.divider()
    st.subheader("📊 Patient Vital Analysis")

    rows = [
        ("🌡 Temperature", f"{tf:.1f} °F", info["Temperature"]),
        ("❤️ Heart Rate", f"{hr:.0f} BPM", info["Heart Rate"]),
        ("🫁 SpO₂", f"{spo2:.0f} %", info["SpO₂"]),
        ("🩸 Blood Pressure", f"{s:.0f}/{d:.0f} mmHg", info["Blood Pressure"]),
        ("🌬 Respiratory Rate", f"{rr:.0f} /min", info["Respiratory Rate"])
    ]
    for name, value, result in rows:
        a, b, c = st.columns([2, 1.5, 3])
        icon = "🟢" if result[0] == "NORMAL" else ("🔴" if result[0] == "HIGH" else "🔵")
        with a: st.write(f"**{name}**")
        with b: st.write(f"**{value}**")
        with c: st.write(f"{icon} **{result[1]}**")

    st.divider()
    a, b = st.columns(2)
    with a: st.metric("Overall Status", status)
    with b: st.metric("Risk Score", f"{risk:.2f}")

    if status == "NORMAL":
        st.success("🟢 NORMAL — All monitored parameters are within the model's normal risk range.")
    elif status == "WARNING":
        st.warning("🟡 WARNING — One or more parameters contribute to an elevated model risk level.")
    else:
        st.error("🔴 CRITICAL — The combined model risk has reached the critical threshold.")

    conditions = abnormal_conditions(info)
    st.subheader("🚨 Detected Conditions")
    if conditions:
        for x in conditions: st.write("• " + x)
    else:
        st.success("No parameter-specific abnormal interpretation detected.")

    # Deduplication prevents Telegram spam on Streamlit reruns.
    key = f"{patient_id}|{tf:.1f}|{hr}|{spo2}|{s}|{d}|{rr}|{status}"
    if "manual_alerts" not in st.session_state:
        st.session_state.manual_alerts = set()
    if status in ("WARNING", "CRITICAL") and key not in st.session_state.manual_alerts:
        if send_alert(patient_id, "Manual Patient Input", status, risk, tf, hr, spo2, s, d, rr, info):
            st.session_state.manual_alerts.add(key)
            st.toast("Telegram alert sent successfully.", icon="📲")

    st.divider()
    st.caption("Reference interpretations are for this research prototype and are not a clinical diagnosis. Interpretation varies with age, measurement method, activity and clinical context.")

else:
    # ========================================================
    # SIMULATION
    # ========================================================
    st.sidebar.subheader("Simulation Scenario")
    scenario = st.sidebar.selectbox("Select Patient Scenario", [
        "Normal Patient", "Fever Progression",
        "Respiratory Deterioration", "Multi-Parameter Deterioration"
    ])

    duration = 60
    time = np.arange(duration)

    if scenario == "Normal Patient":
        temperature, heart_rate, spo2 = np.full(duration,36.8), np.full(duration,76), np.full(duration,98)
        systolic_bp, diastolic_bp, respiratory_rate = np.full(duration,120), np.full(duration,80), np.full(duration,16)
    elif scenario == "Fever Progression":
        temperature = np.r_[np.linspace(36.8,39.5,30), np.linspace(39.5,38.0,30)]
        heart_rate = np.r_[np.linspace(76,125,30), np.linspace(125,90,30)]
        spo2 = np.full(duration,97)
        systolic_bp, diastolic_bp = np.full(duration,125), np.full(duration,82)
        respiratory_rate = np.r_[np.linspace(16,26,30), np.linspace(26,18,30)]
    elif scenario == "Respiratory Deterioration":
        temperature = np.full(duration,37.1)
        heart_rate = np.r_[np.linspace(78,115,30), np.linspace(115,95,30)]
        spo2 = np.r_[np.linspace(98,87,30), np.linspace(87,96,30)]
        systolic_bp, diastolic_bp = np.full(duration,120), np.full(duration,80)
        respiratory_rate = np.r_[np.linspace(16,32,30), np.linspace(32,18,30)]
    else:
        temperature = np.r_[np.linspace(36.8,39.5,30), np.linspace(39.5,37.2,30)]
        heart_rate = np.r_[np.linspace(76,135,30), np.linspace(135,85,30)]
        spo2 = np.r_[np.linspace(98,86,30), np.linspace(86,97,30)]
        systolic_bp = np.r_[np.linspace(120,165,30), np.linspace(165,125,30)]
        diastolic_bp = np.r_[np.linspace(80,100,30), np.linspace(100,82,30)]
        respiratory_rate = np.r_[np.linspace(16,32,30), np.linspace(32,18,30)]

    temperature, heart_rate, spo2 = np.round(temperature,2), np.round(heart_rate,1), np.round(spo2,1)
    systolic_bp, diastolic_bp, respiratory_rate = np.round(systolic_bp,1), np.round(diastolic_bp,1), np.round(respiratory_rate,1)

    risks = np.array([calculate_risk(temperature[i],heart_rate[i],spo2[i],systolic_bp[i],diastolic_bp[i],respiratory_rate[i]) for i in range(duration)])
    statuses = np.array([classify_status(x) for x in risks])

    data = pd.DataFrame({
        "Time (min)":time, "Temperature (°C)":temperature,
        "Heart Rate (BPM)":heart_rate, "SpO₂ (%)":spo2,
        "Systolic BP":systolic_bp, "Diastolic BP":diastolic_bp,
        "Respiratory Rate":respiratory_rate, "Risk Score":risks, "Status":statuses
    })

    idx = np.where(data["Status"] != "NORMAL")[0]
    if len(idx):
        i = int(idx[0])
        alert_tf = float(data["Temperature (°C)"].iloc[i])*9/5+32
        info = interpretations(alert_tf,float(data["Heart Rate (BPM)"].iloc[i]),float(data["SpO₂ (%)"].iloc[i]),float(data["Systolic BP"].iloc[i]),float(data["Diastolic BP"].iloc[i]),float(data["Respiratory Rate"].iloc[i]))
        key = f"{scenario}_{statuses[i]}_{i}"
        if "simulation_alerts" not in st.session_state: st.session_state.simulation_alerts = set()
        if key not in st.session_state.simulation_alerts:
            if send_alert(patient_id, scenario, statuses[i], float(risks[i]), alert_tf, float(data["Heart Rate (BPM)"].iloc[i]), float(data["SpO₂ (%)"].iloc[i]), float(data["Systolic BP"].iloc[i]), float(data["Diastolic BP"].iloc[i]), float(data["Respiratory Rate"].iloc[i]), info):
                st.session_state.simulation_alerts.add(key)

    # Model comparison
    st.divider()
    st.subheader("🔬 Model Comparison")
    temp_scores = np.array([temperature_score(x) for x in data["Temperature (°C)"]])
    temp_status = np.array([classify_status(x) for x in temp_scores])
    mi = np.where(statuses != "NORMAL")[0]
    ti = np.where(temp_status != "NORMAL")[0]
    comparison = pd.DataFrame({
        "Metric":["Detection Model","First Detection Time","Abnormal Time Points","Peak Risk Score"],
        "Temperature-Only Model":["Temperature only",f"{time[ti[0]]} min" if len(ti) else "Not detected",int(np.sum(temp_status!="NORMAL")),f"{temp_scores.max():.2f}"],
        "Multi-Parameter Model":["5 physiological parameters",f"{time[mi[0]]} min" if len(mi) else "Not detected",int(np.sum(statuses!="NORMAL")),f"{risks.max():.2f}"]
    })
    st.dataframe(comparison,use_container_width=True,hide_index=True)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=time,y=temp_scores,mode="lines",name="Temperature-Only Model"))
    fig.add_trace(go.Scatter(x=time,y=risks,mode="lines",name="Multi-Parameter Model"))
    fig.add_hline(y=0.15,line_dash="dash",annotation_text="Warning Threshold")
    fig.add_hline(y=0.40,line_dash="dash",annotation_text="Critical Threshold")
    fig.update_layout(title="Temperature-Only vs Multi-Parameter Risk Detection",xaxis_title="Time (minutes)",yaxis_title="Risk / Severity Score",yaxis_range=[0,1],height=500)
    st.plotly_chart(fig,use_container_width=True)

    # Patient information and latched status
    st.subheader("👤 Patient Information")
    a,b,c = st.columns(3)
    with a: st.write(f"**Patient ID:** {patient_id}")
    with b: st.write("**Monitoring Mode:** Simulation")
    with c: st.write(f"**Scenario:** {scenario}")

    latest = data.iloc[-1]
    latest_tf = float(latest["Temperature (°C)"])*9/5+32
    st.divider()
    st.subheader("📊 Current Vital Signs")
    a,b,c = st.columns(3)
    with a: st.metric("🌡 Temperature",f"{latest_tf:.1f} °F")
    with b: st.metric("❤️ Heart Rate",f"{latest['Heart Rate (BPM)']:.0f} BPM")
    with c: st.metric("🫁 SpO₂",f"{latest['SpO₂ (%)']:.0f} %")
    a,b = st.columns(2)
    with a: st.metric("🩸 Blood Pressure",f"{latest['Systolic BP']:.0f}/{latest['Diastolic BP']:.0f} mmHg")
    with b: st.metric("🌬 Respiratory Rate",f"{latest['Respiratory Rate']:.0f} /min")

    st.divider()
    st.subheader("🧠 Risk Assessment")
    a,b,c = st.columns(3)
    with a: st.metric("Current Risk Score",f"{latest['Risk Score']:.2f}")
    with b: st.metric("Peak Risk Score",f"{risks.max():.2f}")
    with c: st.metric("Critical Time Points",f"{np.sum(statuses=='CRITICAL')} min")

    website_status = "CRITICAL" if "CRITICAL" in statuses else ("WARNING" if "WARNING" in statuses else "NORMAL")
    if website_status == "NORMAL": st.success("🟢 NORMAL — No warning or critical event was detected during the simulation.")
    elif website_status == "WARNING": st.warning("🟡 WARNING — The simulated patient reached an elevated risk level during the monitoring period.")
    else: st.error("🔴 CRITICAL — The simulated patient reached a high risk level during the monitoring period.")

    if website_status != "NORMAL":
        first = int(np.where(statuses!="NORMAL")[0][0])
        st.caption(f"🚨 {website_status} event detected at {time[first]} min | Peak Risk Score: {risks.max():.2f}")
        if latest["Status"] == "NORMAL":
            st.info("The simulated parameters returned toward normal during recovery. The abnormal event remains displayed above.")

    # Graphs
    st.divider()
    st.subheader("📈 Risk Score vs Time")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=time,y=risks,mode="lines+markers",name="Risk Score"))
    fig.add_hline(y=0.15,line_dash="dash",annotation_text="Warning Threshold")
    fig.add_hline(y=0.40,line_dash="dash",annotation_text="Critical Threshold")
    fig.update_layout(xaxis_title="Time (minutes)",yaxis_title="Risk Score",yaxis_range=[0,1],height=450)
    st.plotly_chart(fig,use_container_width=True)

    st.subheader("📊 Vital Sign Trends")
    for col, title, ylabel in [
        ("Temperature (°C)","Temperature Trend","Temperature (°C)"),
        ("Heart Rate (BPM)","Heart Rate Trend","Heart Rate (BPM)"),
        ("SpO₂ (%)","SpO₂ Trend","SpO₂ (%)"),
        ("Respiratory Rate","Respiratory Rate Trend","Respiratory Rate (/min)")
    ]:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=time,y=data[col],mode="lines",name=title))
        fig.update_layout(title=title,xaxis_title="Time (minutes)",yaxis_title=ylabel,height=400)
        st.plotly_chart(fig,use_container_width=True)

    st.subheader("📋 Simulation Dataset")
    st.dataframe(data,use_container_width=True)

    st.caption("This simulation uses predefined physiological ranges, weights and risk thresholds for research experimentation. It is not intended for clinical diagnosis.")