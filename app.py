import streamlit as st
import joblib
import uuid
from datetime import datetime
import sqlite3

import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
import hashlib

# ==============================
# DATABASE SETUP
# ==============================

conn = sqlite3.connect("transactions.db", check_same_thread=False)
c = conn.cursor()

# ==============================
# USERS TABLE (FOR ADMIN LOGIN)
# ==============================

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT
)
""")
conn.commit()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# create default admin
c.execute("INSERT OR IGNORE INTO users VALUES (?, ?)",
          ("admin", hash_password("daz123")))
conn.commit()

# ==============================
# LOGIN
# ==============================

st.sidebar.title("🔐 Admin Login")

username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")

if st.sidebar.button("Login"):
    hashed = hash_password(password)
    c.execute("SELECT * FROM users WHERE username=? AND password=?",
              (username, hashed))
    user = c.fetchone()

    if user:
        st.session_state["admin"] = True
        st.sidebar.success("Login successful")
    else:
        st.sidebar.error("Invalid credentials")
#------------------------------------------------------------------------------------------------------------
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
    #------------------------------------------------------------
# =====================================
# ADMIN DASHBOARD
# =====================================

if st.session_state.get("admin"):

    st.markdown("---")
    st.header("📊 ADMIN FRAUD DASHBOARD")

    # Auto refresh every 15 seconds
    st_autorefresh(interval=15000, key="refresh")

    df = pd.read_sql_query("SELECT * FROM transactions", conn)

    if not df.empty:

        st.subheader("📋 Transaction Table")
        st.dataframe(df)

        # DOWNLOAD CSV
        st.download_button(
            "⬇ Download CSV",
            df.to_csv(index=False),
            "transactions.csv",
            "text/csv"
        )

        # DELETE TRANSACTION
        delete_id = st.selectbox("Select Transaction ID to Delete", df["id"])
        if st.button("Delete Selected Transaction"):
            c.execute("DELETE FROM transactions WHERE id=?", (delete_id,))
            conn.commit()
            st.success("Transaction Deleted")

        # PIE CHART
        st.subheader("🥧 Risk Distribution")
        fig_pie = px.pie(df, names="risk_level")
        st.plotly_chart(fig_pie, use_container_width=True)

        # FRAUD TREND
        st.subheader("📈 Fraud Probability Trend")
        df_sorted = df.sort_values("timestamp")
        fig_line = px.line(df_sorted, y="fraud_probability")
        st.plotly_chart(fig_line, use_container_width=True)

    else:
        st.warning("No transactions recorded yet.")

# =====================================
# POWER BI EXPORT
# =====================================
