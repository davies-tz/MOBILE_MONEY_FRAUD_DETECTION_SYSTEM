import streamlit as st
import sqlite3
import joblib
import uuid
import hashlib
import pandas as pd
import plotly.express as px
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# =====================================
# PAGE CONFIG
# =====================================
st.set_page_config(page_title="Fraud Detection System", layout="wide")

# =====================================
# DATABASE CONNECTION
# =====================================
conn = sqlite3.connect("transactions.db", check_same_thread=False)
c = conn.cursor()

# Users Table
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT,
    role TEXT
)
""")

conn.commit()

# Transactions Table
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
    latitude REAL,
    longitude REAL
)
""")


# =====================================
# PASSWORD HASH FUNCTION
# =====================================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Create default admin
c.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?)",
          ("admin", hash_password("daz123"), "admin"))
conn.commit()

# =====================================
# LOGIN SYSTEM
# =====================================
st.sidebar.title("🔐 Admin Login")

username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")

if st.sidebar.button("Login"):
    hashed = hash_password(password)
    c.execute("SELECT * FROM users WHERE username=? AND password=?",
              (username, hashed))
    user = c.fetchone()

    if user:
        st.session_state["logged_in"] = True
        st.session_state["role"] = user[2]
        st.sidebar.success("Login successful")
    else:
        st.sidebar.error("Invalid credentials")

# =====================================
# MAIN APP
# =====================================
if st.session_state.get("logged_in"):

    st.title("🇹🇿 Mobile Money Fraud Detection Dashboard")

    # Auto refresh every 15 seconds
    st_autorefresh(interval=15000, key="refresh")

    model = joblib.load("model.pkl")

    # -----------------------------
    # User Transaction Input
    # -----------------------------
    st.header("💳 Enter Transaction")

    amount = st.number_input("Amount (TZS)", min_value=100.0)
    sender_age = st.number_input("Sender Age", min_value=5, max_value=90)
    location_risk = st.slider("Location Risk (0=Low,1=High)", 0, 1)
    latitude = st.number_input("Latitude", value=-6.8)
    longitude = st.number_input("Longitude", value=39.2)

    if st.button("Analyze Transaction"):

        input_data = [[amount, sender_age, 0, 0, 1, location_risk]]
        prediction = model.predict(input_data)[0]
        fraud_probability = model.predict_proba(input_data)[0][1]

        if fraud_probability > 0.7:
            risk_level = "HIGH RISK"
        elif fraud_probability > 0.4:
            risk_level = "MEDIUM RISK"
        else:
            risk_level = "LOW RISK"

        if prediction == 1:
            st.error("⚠ FRAUD DETECTED")
        else:
            st.success("✅ SAFE")

        transaction_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        c.execute("""
        INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            transaction_id,
            timestamp,
            amount,
            sender_age,
            location_risk,
            fraud_probability,
            risk_level,
            int(prediction),
            latitude,
            longitude
        ))

        conn.commit()
        st.info("Transaction recorded successfully.")

    # -----------------------------
    # Admin Dashboard
    # -----------------------------
    st.markdown("---")
    st.header("📊 Admin Dashboard")

    df = pd.read_sql_query("SELECT * FROM transactions", conn)

    if not df.empty:

        st.subheader("📋 Transaction Table")
        st.dataframe(df)

        # -----------------------------
        # Download CSV
        # -----------------------------
        st.download_button(
            "⬇ Download CSV",
            df.to_csv(index=False),
            "transactions.csv",
            "text/csv"
        )

        # -----------------------------
        # Delete Transaction
        # -----------------------------
        delete_id = st.selectbox("Select Transaction ID to Delete", df["id"])
        if st.button("Delete Selected Transaction"):
            c.execute("DELETE FROM transactions WHERE id=?", (delete_id,))
            conn.commit()
            st.success("Transaction Deleted")

        # -----------------------------
        # Pie Chart
        # -----------------------------
        st.subheader("🥧 Risk Distribution")
        fig_pie = px.pie(df, names="risk_level", title="Risk Levels")
        st.plotly_chart(fig_pie, use_container_width=True)

        # -----------------------------
        # Fraud Heatmap
        # -----------------------------
        st.subheader("🗺 Fraud Heatmap")
        fig_map = px.density_mapbox(
            df,
            lat="latitude",
            lon="longitude",
            z="fraud_probability",
            radius=10,
            center=dict(lat=-6.8, lon=39.2),
            zoom=5,
            mapbox_style="open-street-map"
        )
        st.plotly_chart(fig_map, use_container_width=True)

        # -----------------------------
        # Monthly PDF Report
        # -----------------------------
        def generate_report():
            doc = SimpleDocTemplate("monthly_report.pdf")
            elements = []
            styles = getSampleStyleSheet()

            total = len(df)
            frauds = df["prediction"].sum()

            elements.append(Paragraph("Monthly Fraud Report", styles["Title"]))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(f"Total Transactions: {total}", styles["Normal"]))
            elements.append(Paragraph(f"Total Fraud Cases: {frauds}", styles["Normal"]))

            doc.build(elements)

        if st.button("📄 Generate Monthly PDF Report"):
            generate_report()
            st.success("Report Generated (monthly_report.pdf)")

        # -----------------------------
        # Power BI CSV Export
        # -----------------------------
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['Year'] = df['timestamp'].dt.year
        df['Month'] = df['timestamp'].dt.month
        df.to_csv("powerbi_data.csv", index=False)
        st.info("Power BI CSV updated (powerbi_data.csv)")

else:
    st.warning("Please login to access dashboard.")
