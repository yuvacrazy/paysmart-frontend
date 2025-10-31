import streamlit as st
import requests
import plotly.graph_objects as go
import time

# ------------------------------
# Config
# ------------------------------
API_URL = "https://ai-powered-salary-prediction-system.onrender.com/predict"  # your backend URL
API_KEY = None  # Leave None if backend auth is disabled

HEADERS = {"Content-Type": "application/json"}
if API_KEY:
    HEADERS["x-api-key"] = API_KEY

st.set_page_config(page_title="SmartPay | Salary Prediction", page_icon="💼", layout="wide")

st.markdown("<h1 style='text-align:center;color:#00c6ff;'>SmartPay – AI Salary Intelligence</h1>", unsafe_allow_html=True)
st.write("")

# ------------------------------
# Inputs
# ------------------------------
col1, col2, col3 = st.columns(3)
with col1:
    age = st.number_input("Age", 17, 100, 28)
    education = st.selectbox("Education", ["High School", "Bachelor’s", "Master’s", "PhD"])
with col2:
    job_title = st.text_input("Job Title", "Software Engineer")
    hours_per_week = st.slider("Hours per Week", 20, 100, 40)
with col3:
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    marital_status = st.selectbox("Marital Status", ["Single", "Married", "Divorced"])

# ------------------------------
# Prediction Button
# ------------------------------
if st.button("🔍 Predict Salary"):
    with st.spinner("Predicting..."):
        time.sleep(1)
        data = {
            "age": age,
            "education": education,
            "job_title": job_title,
            "hours_per_week": hours_per_week,
            "gender": gender,
            "marital_status": marital_status
        }
        try:
            response = requests.post(API_URL, json=data, headers=HEADERS)
            if response.status_code == 200:
                salary = response.json()["predicted_salary_usd"]
                st.success(f"💰 Predicted Salary: ${salary:,.2f}")
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=salary,
                    title={'text': "Annual Salary (USD)"},
                    gauge={'axis': {'range': [0, 250000]}, 'bar': {'color': "#00c6ff"}}
                ))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error(f"API Error: {response.status_code} - {response.text}")
        except Exception as e:
            st.error(f"Connection failed: {e}")
