import streamlit as st
import joblib
import uuid
from datetime import datetime
import pandas as pd
import random
import math
import sqlite3

# DATABASE SETUP

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
    prediction INTEGER
)
""")

conn.commit()


# PAGE TITLE

st.title("🇹🇿 MOBILE MONEY FRAUD DETECTION SYSTEM")

# LOAD MODEL
model = joblib.load("model.pkl")

st.header("Enter Transaction Details")


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
    }
    </style>
    """,
    unsafe_allow_html=True
)

# CUSTOMER INPUTS

amount = st.number_input("Transaction Amount", min_value=0)

sender_age = st.number_input(
    "Sender Age",
    min_value=5,
    max_value=90,
    step=1
)

receiver_new_account = st.selectbox("Receiver New Account?", ["No", "Yes"])
device_change = st.selectbox("Device Change?", ["No", "Yes"])

transaction_frequency = st.number_input(
    "Transaction Frequency",
    min_value=0,
    max_value=50,
    step=1
)    app.py yake ndo hii je inashida
