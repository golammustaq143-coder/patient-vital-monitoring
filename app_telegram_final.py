import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Patient Vital Monitoring System",
    page_icon="❤️",
    layout="wide"
)

# ============================================================
# TITLE
# ============================================================

st.title("❤️ Multi-Parameter Patient Vital Monitoring System")

st.write(
    "Simulation-based multi-parameter physiological monitoring "
    "and early warning framework."
)

st.divider()

# ============================================================
# REFERENCE RANGES
# ============================================================

TEMP_MIN = 36.1
TEMP_MAX = 37.5

HR_MIN = 60
HR_MAX = 100

SPO2_MIN = 95

SYS_BP_MIN = 90
SYS_BP_MAX = 129

DIA_BP_MIN = 60
DIA_BP_MAX = 84

RR_MIN = 12
RR_MAX = 20

# ============================================================
# WEIGHTS
# ============================================================

W_TEMP = 0.15
W_HR = 0.20
W_SPO2 = 0.30
W_BP = 0.20
W_RR = 0.15

# ============================================================
# SEVERITY FUNCTIONS
# ============================================================

def temperature_score(value):

    if TEMP_MIN <= value <= TEMP_MAX:
        return 0.0

    elif 37.5 < value <= 38.0:
        return 0.3

    elif 38.0 < value <= 39.0:
        return 0.6

    elif value > 39.0:
        return 1.0

    else:
        return 0.6


def heart_rate_score(value):

    if HR_MIN <= value <= HR_MAX:
        return 0.0

    elif 100 < value <= 110:
        return 0.3

    elif 110 < value <= 130:
        return 0.6

    elif value > 130:
        return 1.0

    else:
        return 0.6


def spo2_score(value):

    if value >= SPO2_MIN:
        return 0.0

    elif 93 <= value < 95:
        return 0.3

    elif 90 <= value < 93:
        return 0.6

    else:
        return 1.0


def blood_pressure_score(systolic, diastolic):

    score = 0.0

    if (
        SYS_BP_MIN <= systolic <= SYS_BP_MAX
        and DIA_BP_MIN <= diastolic <= DIA_BP_MAX
    ):
        return 0.0

    if systolic > SYS_BP_MAX or diastolic > DIA_BP_MAX:
        score = 0.3

    if systolic > 150 or diastolic > 95:
        score = 0.6

    if systolic > 180 or diastolic > 120:
        score = 1.0

    if systolic < SYS_BP_MIN or diastolic < DIA_BP_MIN:
        score = max(score, 0.3)

    return min(score, 1.0)


def respiratory_score(value):

    if RR_MIN <= value <= RR_MAX:
        return 0.0

    elif 20 < value <= 25:
        return 0.3

    elif 25 < value <= 30:
        return 0.6

    elif value > 30:
        return 1.0

    else:
        return 0.6


# ============================================================
# RISK CALCULATION
# ============================================================

def calculate_risk(temp, hr, spo2, systolic, diastolic, rr):

    temp_s = temperature_score(temp)
    hr_s = heart_rate_score(hr)
    spo2_s = spo2_score(spo2)
    bp_s = blood_pressure_score(systolic, diastolic)
    rr_s = respiratory_score(rr)

    risk = (
        W_TEMP * temp_s
        + W_HR * hr_s
        + W_SPO2 * spo2_s
        + W_BP * bp_s
        + W_RR * rr_s
    )

    return risk


def classify_status(risk):

    if risk < 0.15:
        return "NORMAL"

    elif risk < 0.40:
        return "WARNING"

    else:
        return "CRITICAL"


# ============================================================
# TELEGRAM ALERT SYSTEM
# ============================================================

def send_telegram_message(message):

    try:
        bot_token = st.secrets["TELEGRAM_BOT_TOKEN"]
        chat_id = st.secrets["TELEGRAM_CHAT_ID"]

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        response = requests.post(
            url,
            data={"chat_id": chat_id, "text": message},
            timeout=10
        )

        return response.ok

    except Exception:
        return False


def send_patient_status_alert(
    previous_status, new_status, patient_id, scenario, alert_time,
    temp, hr, spo2, systolic, diastolic, rr, risk
):

    if new_status == "WARNING":
        message = (
            "🟡 PATIENT STATUS ALERT\n\n"
            f"Patient ID: {patient_id}\n"
            f"Status: {previous_status} → {new_status}\n"
            f"Scenario: {scenario}\n\n"
            f"Time: {alert_time} min\n"
            f"Risk Score: {risk:.2f}\n\n"
            f"Temperature: {temp:.1f} °C\n"
            f"Heart Rate: {hr:.0f} BPM\n"
            f"SpO₂: {spo2:.0f}%\n"
            f"Blood Pressure: {systolic:.0f}/{diastolic:.0f} mmHg\n"
            f"Respiratory Rate: {rr:.0f}/min\n\n"
            "Please review the patient monitoring status."
        )
    elif new_status == "CRITICAL":
        message = (
            "🔴 CRITICAL PATIENT ALERT\n\n"
            f"Patient ID: {patient_id}\n"
            f"Status: {previous_status} → {new_status}\n"
            f"Scenario: {scenario}\n\n"
            f"Time: {alert_time} min\n"
            f"Risk Score: {risk:.2f}\n\n"
            f"Temperature: {temp:.1f} °C\n"
            f"Heart Rate: {hr:.0f} BPM\n"
            f"SpO₂: {spo2:.0f}%\n"
            f"Blood Pressure: {systolic:.0f}/{diastolic:.0f} mmHg\n"
            f"Respiratory Rate: {rr:.0f}/min\n\n"
            "Immediate review is recommended."
        )
    else:
        return False

    return send_telegram_message(message)

# ============================================================
# SIMULATION SCENARIO
# ============================================================

st.sidebar.header("⚙️ Simulation Settings")

scenario = st.sidebar.selectbox(
    "Select Patient Scenario",
    [
        "Normal Patient",
        "Fever Progression",
        "Respiratory Deterioration",
        "Multi-Parameter Deterioration"
    ]
)

duration = 60

time = np.arange(duration)

# ============================================================
# GENERATE SIMULATED DATA
# ============================================================

if scenario == "Normal Patient":

    temperature = np.full(duration, 36.8)
    heart_rate = np.full(duration, 76)
    spo2 = np.full(duration, 98)
    systolic_bp = np.full(duration, 120)
    diastolic_bp = np.full(duration, 80)
    respiratory_rate = np.full(duration, 16)


elif scenario == "Fever Progression":

    temperature = np.concatenate([
        np.linspace(36.8, 39.5, 30),
        np.linspace(39.5, 38.0, 30)
    ])

    heart_rate = np.concatenate([
        np.linspace(76, 125, 30),
        np.linspace(125, 90, 30)
    ])

    spo2 = np.full(duration, 97)

    systolic_bp = np.full(duration, 125)
    diastolic_bp = np.full(duration, 82)

    respiratory_rate = np.concatenate([
        np.linspace(16, 26, 30),
        np.linspace(26, 18, 30)
    ])


elif scenario == "Respiratory Deterioration":

    temperature = np.full(duration, 37.1)

    heart_rate = np.concatenate([
        np.linspace(78, 115, 30),
        np.linspace(115, 95, 30)
    ])

    spo2 = np.concatenate([
        np.linspace(98, 87, 30),
        np.linspace(87, 96, 30)
    ])

    systolic_bp = np.full(duration, 120)
    diastolic_bp = np.full(duration, 80)

    respiratory_rate = np.concatenate([
        np.linspace(16, 32, 30),
        np.linspace(32, 18, 30)
    ])


else:

    temperature = np.concatenate([
        np.linspace(36.8, 39.5, 30),
        np.linspace(39.5, 37.2, 30)
    ])

    heart_rate = np.concatenate([
        np.linspace(76, 135, 30),
        np.linspace(135, 85, 30)
    ])

    spo2 = np.concatenate([
        np.linspace(98, 86, 30),
        np.linspace(86, 97, 30)
    ])

    systolic_bp = np.concatenate([
        np.linspace(120, 165, 30),
        np.linspace(165, 125, 30)
    ])

    diastolic_bp = np.concatenate([
        np.linspace(80, 100, 30),
        np.linspace(100, 82, 30)
    ])

    respiratory_rate = np.concatenate([
        np.linspace(16, 32, 30),
        np.linspace(32, 18, 30)
    ])


# ============================================================
# ROUND DATA
# ============================================================

temperature = np.round(temperature, 2)
heart_rate = np.round(heart_rate, 1)
spo2 = np.round(spo2, 1)
systolic_bp = np.round(systolic_bp, 1)
diastolic_bp = np.round(diastolic_bp, 1)
respiratory_rate = np.round(respiratory_rate, 1)


# ============================================================
# CALCULATE RISK FOR EVERY TIME POINT
# ============================================================

risk_scores = []

statuses = []

for i in range(duration):

    risk = calculate_risk(
        temperature[i],
        heart_rate[i],
        spo2[i],
        systolic_bp[i],
        diastolic_bp[i],
        respiratory_rate[i]
    )

    risk_scores.append(risk)

    statuses.append(
        classify_status(risk)
    )


risk_scores = np.array(risk_scores)


# ============================================================
# DATAFRAME
# ============================================================

data = pd.DataFrame({
    "Time (min)": time,
    "Temperature (°C)": temperature,
    "Heart Rate (BPM)": heart_rate,
    "SpO₂ (%)": spo2,
    "Systolic BP": systolic_bp,
    "Diastolic BP": diastolic_bp,
    "Respiratory Rate": respiratory_rate,
    "Risk Score": risk_scores,
    "Status": statuses
})


# ============================================================
# AUTOMATIC PATIENT STATUS ALERT
# ============================================================

# Notify only when the simulated status first changes from NORMAL
# to WARNING or CRITICAL for the selected scenario.
patient_id = "P001"
abnormal_indices = np.where(data["Status"] != "NORMAL")[0]

if len(abnormal_indices) > 0:
    alert_index = int(abnormal_indices[0])
    alert_status = data["Status"].iloc[alert_index]
    alert_key = f"{scenario}_{alert_status}_{alert_index}"

    if "sent_alerts" not in st.session_state:
        st.session_state.sent_alerts = set()

    if alert_key not in st.session_state.sent_alerts:
        alert_success = send_patient_status_alert(
            previous_status="NORMAL",
            new_status=alert_status,
            patient_id=patient_id,
            scenario=scenario,
            alert_time=int(data["Time (min)"].iloc[alert_index]),
            temp=float(data["Temperature (°C)"].iloc[alert_index]),
            hr=float(data["Heart Rate (BPM)"].iloc[alert_index]),
            spo2=float(data["SpO₂ (%)"].iloc[alert_index]),
            systolic=float(data["Systolic BP"].iloc[alert_index]),
            diastolic=float(data["Diastolic BP"].iloc[alert_index]),
            rr=float(data["Respiratory Rate"].iloc[alert_index]),
            risk=float(data["Risk Score"].iloc[alert_index])
        )

        if alert_success:
            st.session_state.sent_alerts.add(alert_key)
# ============================================================
# MODEL COMPARISON
# ============================================================

st.divider()

st.subheader("🔬 Model Comparison")

st.write(
    "Comparison between a temperature-only detection model "
    "and the proposed multi-parameter risk model."
)


# ------------------------------------------------------------
# TEMPERATURE-ONLY MODEL
# ------------------------------------------------------------

temperature_only_scores = []
temperature_only_status = []


for temp in data["Temperature (°C)"]:

    score = temperature_score(temp)

    temperature_only_scores.append(score)

    if score < 0.15:
        status = "NORMAL"

    elif score < 0.40:
        status = "WARNING"

    else:
        status = "CRITICAL"

    temperature_only_status.append(status)


temperature_only_scores = np.array(
    temperature_only_scores
)


# ------------------------------------------------------------
# DETECTION TIME
# ------------------------------------------------------------

multi_warning_indices = np.where(
    data["Status"] != "NORMAL"
)[0]


temp_warning_indices = np.where(
    np.array(temperature_only_status) != "NORMAL"
)[0]


if len(multi_warning_indices) > 0:

    multi_detection_time = int(
        data["Time (min)"].iloc[multi_warning_indices[0]]
    )

else:

    multi_detection_time = None


if len(temp_warning_indices) > 0:

    temp_detection_time = int(
        data["Time (min)"].iloc[temp_warning_indices[0]]
    )

else:

    temp_detection_time = None


# ------------------------------------------------------------
# ABNORMAL TIME POINTS
# ------------------------------------------------------------

multi_abnormal_points = np.sum(
    data["Status"] != "NORMAL"
)


temp_abnormal_points = np.sum(
    np.array(temperature_only_status) != "NORMAL"
)


# ------------------------------------------------------------
# PEAK RISK
# ------------------------------------------------------------

multi_peak_risk = data["Risk Score"].max()

temp_peak_risk = temperature_only_scores.max()


# ------------------------------------------------------------
# COMPARISON TABLE
# ------------------------------------------------------------

comparison_data = pd.DataFrame({

    "Metric": [
        "Detection Model",
        "First Detection Time",
        "Abnormal Time Points",
        "Peak Risk Score"
    ],

    "Temperature-Only Model": [

        "Temperature only",

        f"{temp_detection_time} min"
        if temp_detection_time is not None
        else "Not detected",

        int(temp_abnormal_points),

        f"{temp_peak_risk:.2f}"
    ],

    "Multi-Parameter Model": [

        "5 physiological parameters",

        f"{multi_detection_time} min"
        if multi_detection_time is not None
        else "Not detected",

        int(multi_abnormal_points),

        f"{multi_peak_risk:.2f}"
    ]
})


st.dataframe(
    comparison_data,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# MODEL COMPARISON GRAPH
# ============================================================

st.subheader("📊 Detection Model Comparison")

fig_compare = go.Figure()


# Temperature-only model
fig_compare.add_trace(
    go.Scatter(
        x=data["Time (min)"],
        y=temperature_only_scores,
        mode="lines",
        name="Temperature-Only Model"
    )
)


# Multi-parameter model
fig_compare.add_trace(
    go.Scatter(
        x=data["Time (min)"],
        y=data["Risk Score"],
        mode="lines",
        name="Multi-Parameter Model"
    )
)


# Warning threshold
fig_compare.add_hline(
    y=0.15,
    line_dash="dash",
    annotation_text="Warning Threshold"
)


# Critical threshold
fig_compare.add_hline(
    y=0.40,
    line_dash="dash",
    annotation_text="Critical Threshold"
)


fig_compare.update_layout(
    title="Temperature-Only vs Multi-Parameter Risk Detection",
    xaxis_title="Time (minutes)",
    yaxis_title="Risk / Severity Score",
    yaxis_range=[0, 1],
    height=500
)


st.plotly_chart(
    fig_compare,
    use_container_width=True
)


# ============================================================
# RESEARCH INTERPRETATION
# ============================================================

st.subheader("📝 Simulation Interpretation")


if scenario == "Normal Patient":

    st.info(
        "The simulated patient remains within the defined "
        "reference ranges. Both models are expected to "
        "maintain a normal state."
    )


elif scenario == "Fever Progression":

    st.info(
        "The temperature-only model responds primarily to "
        "the rise in body temperature, while the multi-parameter "
        "model also incorporates associated changes in other "
        "physiological parameters."
    )


elif scenario == "Respiratory Deterioration":

    st.info(
        "The multi-parameter model incorporates SpO₂ and "
        "respiratory-rate changes, allowing the simulation "
        "to represent deterioration that is not primarily "
        "temperature-driven."
    )


else:

    st.info(
        "The multi-parameter model integrates simultaneous "
        "changes across several physiological parameters. "
        "This scenario is designed to evaluate the behaviour "
        "of the combined risk-scoring framework."
    )

# ============================================================
# PATIENT INFORMATION
# ============================================================

st.subheader("👤 Patient Information")

col1, col2, col3 = st.columns(3)

with col1:
    st.write("**Patient ID:** P001")

with col2:
    st.write("**Monitoring Mode:** Simulation")

with col3:
    st.write(f"**Scenario:** {scenario}")


st.divider()


# ============================================================
# CURRENT PATIENT VALUES
# ============================================================

st.subheader("📊 Current Vital Signs")

latest = data.iloc[-1]

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "🌡 Temperature",
        f"{latest['Temperature (°C)']:.1f} °C"
    )

with col2:
    st.metric(
        "❤️ Heart Rate",
        f"{latest['Heart Rate (BPM)']:.0f} BPM"
    )

with col3:
    st.metric(
        "🫁 SpO₂",
        f"{latest['SpO₂ (%)']:.0f} %"
    )


col4, col5 = st.columns(2)

with col4:
    st.metric(
        "🩸 Blood Pressure",
        f"{latest['Systolic BP']:.0f}/{latest['Diastolic BP']:.0f} mmHg"
    )

with col5:
    st.metric(
        "🫁 Respiratory Rate",
        f"{latest['Respiratory Rate']:.0f} /min"
    )


st.divider()


# ============================================================
# RISK SUMMARY
# ============================================================

st.subheader("🧠 Risk Assessment")

risk_col1, risk_col2, risk_col3 = st.columns(3)

with risk_col1:

    st.metric(
        "Current Risk Score",
        f"{latest['Risk Score']:.2f}"
    )

with risk_col2:

    st.metric(
        "Peak Risk Score",
        f"{risk_scores.max():.2f}"
    )

with risk_col3:

    critical_count = np.sum(data["Status"] == "CRITICAL")

    st.metric(
        "Critical Time Points",
        f"{critical_count} min"
    )


# ============================================================
# CURRENT STATUS
# ============================================================

if latest["Status"] == "NORMAL":

    st.success(
        "🟢 NORMAL — Simulated physiological parameters "
        "are within the defined reference ranges."
    )

elif latest["Status"] == "WARNING":

    st.warning(
        "🟡 WARNING — The simulated patient shows an "
        "elevated risk level."
    )

else:

    st.error(
        "🔴 CRITICAL — The simulated patient shows a "
        "high risk level in the model."
    )


st.divider()


# ============================================================
# RISK SCORE GRAPH
# ============================================================

st.subheader("📈 Risk Score vs Time")

fig_risk = go.Figure()

fig_risk.add_trace(
    go.Scatter(
        x=data["Time (min)"],
        y=data["Risk Score"],
        mode="lines+markers",
        name="Risk Score"
    )
)

fig_risk.add_hline(
    y=0.15,
    line_dash="dash",
    annotation_text="Warning Threshold"
)

fig_risk.add_hline(
    y=0.40,
    line_dash="dash",
    annotation_text="Critical Threshold"
)

fig_risk.update_layout(
    xaxis_title="Time (minutes)",
    yaxis_title="Risk Score",
    yaxis_range=[0, 1],
    height=450
)

st.plotly_chart(
    fig_risk,
    use_container_width=True
)


# ============================================================
# VITAL SIGN TRENDS
# ============================================================

st.subheader("📊 Vital Sign Trends")

fig_vitals = go.Figure()

fig_vitals.add_trace(
    go.Scatter(
        x=data["Time (min)"],
        y=data["Temperature (°C)"],
        mode="lines",
        name="Temperature"
    )
)

fig_vitals.update_layout(
    xaxis_title="Time (minutes)",
    yaxis_title="Temperature (°C)",
    height=400
)

st.plotly_chart(
    fig_vitals,
    use_container_width=True
)


fig_hr = go.Figure()

fig_hr.add_trace(
    go.Scatter(
        x=data["Time (min)"],
        y=data["Heart Rate (BPM)"],
        mode="lines",
        name="Heart Rate"
    )
)

fig_hr.update_layout(
    xaxis_title="Time (minutes)",
    yaxis_title="Heart Rate (BPM)",
    height=400
)

st.plotly_chart(
    fig_hr,
    use_container_width=True
)


fig_spo2 = go.Figure()

fig_spo2.add_trace(
    go.Scatter(
        x=data["Time (min)"],
        y=data["SpO₂ (%)"],
        mode="lines",
        name="SpO₂"
    )
)

fig_spo2.update_layout(
    xaxis_title="Time (minutes)",
    yaxis_title="SpO₂ (%)",
    height=400
)

st.plotly_chart(
    fig_spo2,
    use_container_width=True
)


fig_rr = go.Figure()

fig_rr.add_trace(
    go.Scatter(
        x=data["Time (min)"],
        y=data["Respiratory Rate"],
        mode="lines",
        name="Respiratory Rate"
    )
)

fig_rr.update_layout(
    xaxis_title="Time (minutes)",
    yaxis_title="Respiratory Rate (/min)",
    height=400
)

st.plotly_chart(
    fig_rr,
    use_container_width=True
)


# ============================================================
# SIMULATION DATA
# ============================================================

st.subheader("📋 Simulation Dataset")

st.dataframe(
    data,
    use_container_width=True
)


st.caption(
    "This simulation uses predefined physiological ranges, "
    "weights, and risk thresholds for research experimentation. "
    "It is not intended for clinical diagnosis."
)