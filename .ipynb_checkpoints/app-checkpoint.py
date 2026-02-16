
import streamlit as st
import joblib

st.title("MOBILE MONEY FRAUD DETECTION SYSTEM")

model = joblib.load("model.pkl")

features = []
features.append(st.number_input("Transaction Amount"))
features.append(st.number_input("Transaction Time"))
features.append(st.number_input("Sender Age"))
features.append(st.number_input("Receiver New Account (0/1)"))
features.append(st.number_input("Location Risk Score"))
features.append(st.number_input("Device Change (0/1)"))
features.append(st.number_input("Transaction Frequency"))

if st.button("Predict"):
    prediction = model.predict([features])
    if prediction[0] == 1:
        st.error("⚠️ Fraudulent Transaction Detected!")
    else:
        st.success("✅ Legitimate Transaction")
