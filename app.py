import streamlit as st
import joblib
import uuid
from datetime import datetime
import sqlite3

# ==============================
# DATABASE SETUP
# ==============================

conn = sqlite3.connect("transactions.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id TEXT,
    timestamp TEXT,
    amount REAL,
    sender_age INTEGER,
    location_risk INTEGER,
    fraud_probability REAL,
    risk_level TEXT,
    prediction INTEGER,
    reason TEXT
)
""")
conn.commit()

# ==============================
# PAGE CONFIG
# ==============================

st.set_page_config(page_title="Fraud Detection System", layout="centered")

# DARK THEME
st.markdown(
    """
    <style>
    .stApp {
        background-color: #001f4d;
        color: white;
    }
    button[kind="primary"] {
        background-color: #1E90FF;
        color: white;
        font-size: 18px;
        padding: 10px 20px;
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🇹🇿 MOBILE MONEY FRAUD DETECTION SYSTEM")
st.write("AI-powered fraud detection for Tanzania Mobile Money Transactions")

# ==============================
# LOAD MODEL
# ==============================

model = joblib.load("model.pkl")
st.write("Model expects:", model.n_features_in_, "features")

st.header("Enter Transaction Details")

# ==============================
# INPUTS
# ==============================

amount = st.number_input(
    "Transaction Amount (TZS)",
    min_value=100.0,
    step=100.0
)

sender_age = st.number_input(
    "Sender Age",
    min_value=5,
    max_value=90,
    step=1
)

receiver_new_account = st.selectbox("Receiver New Account?", ["No", "Yes"])
device_change = st.selectbox("Device Change?", ["No", "Yes"])

transaction_frequency = st.number_input(
    "Transaction Frequency (per day)",
    min_value=0,
    max_value=50,
    step=1
)

location_risk = st.slider("Location Risk Level (0 = Low Risk Area, 1 = High Risk Area)", 0, 1)

# Convert categorical inputs
receiver_new_account = 1 if receiver_new_account == "Yes" else 0
device_change = 1 if device_change == "Yes" else 0


# ==============================
# PREDICTION BUTTON
# ==============================

if st.button("🔍 Analyze Transaction", type="primary"):

    fraud_probability = 0
    prediction = 0
    risk_level = "LOW RISK"
    reason = "Model-based evaluation"

    # ==================================
    # BUSINESS RULES VALIDATION
    # ==================================

    if amount > 50000000:
        prediction = 1
        fraud_probability = 0.99
        risk_level = "HIGH RISK"
        reason = "Suspiciously large transaction amount entered at once."

    elif sender_age < 18:
        prediction = 1
        fraud_probability = 0.95
        risk_level = "HIGH RISK"
        reason = "Underage user not legally allowed to perform mobile money transactions."

    else:
        # ==================================
        # MODEL PREDICTION
        # ==================================
        input_data = [[
            amount,
            sender_age,
            receiver_new_account,
            device_change,
            transaction_frequency,
            location_risk
        ]]

        prediction = model.predict(input_data)[0]

        if hasattr(model, "predict_proba"):
            fraud_probability = model.predict_proba(input_data)[0][1]
        else:
            fraud_probability = float(prediction)

        # Risk Level classification
        if fraud_probability > 0.7:
            risk_level = "HIGH RISK"
        elif fraud_probability > 0.4:
            risk_level = "MEDIUM RISK"
        else:
            risk_level = "LOW RISK"

        reason = "AI model analysis based on transaction behavior."

    # ==================================
    # DISPLAY RESULTS
    # ==================================

    if prediction == 1:
        st.error("⚠ FRAUD DETECTED!")
    else:
        st.success("✅ Transaction is SAFE")

    st.write(f"**Fraud Probability:** {fraud_probability:.2f}")
    st.write(f"**Risk Level:** {risk_level}")
    st.write(f"**Reason:** {reason}")

    # ==================================
    # SAVE TO DATABASE
    # ==================================

    transaction_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    c.execute("""
        INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        transaction_id,
        timestamp,
        amount,
        sender_age,
        location_risk,
        fraud_probability,
        risk_level,
        int(prediction),
        reason
    ))

    conn.commit()

    st.info("Transaction recorded successfully.")
