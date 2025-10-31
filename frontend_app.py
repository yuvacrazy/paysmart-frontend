import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
import time
from datetime import datetime
import tempfile
import os

# ----------------------------
# CONFIG
# ----------------------------
BACKEND_URL = "https://smartpay-ai-backend.onrender.com"  # <<-- your backend
API_KEY = None  # set to string if your backend requires API key
HEADERS = {"Content-Type": "application/json"}
if API_KEY:
    HEADERS["x-api-key"] = API_KEY

st.set_page_config(page_title="SmartPay • AI Salary", page_icon="💼", layout="wide")

# ----------------------------
# CSS / STYLES
# ----------------------------
st.markdown(
    """
    <style>
    /* page background */
    .stApp {
      background: radial-gradient(circle at 10% 10%, #020617 0%, #071125 30%, #0b1220 100%);
      color: #e6f7ff;
    }

    /* animated header */
    .hero {
      background: linear-gradient(90deg, rgba(2,12,27,0.9), rgba(0,118,255,0.08));
      border-radius: 16px;
      padding: 28px;
      box-shadow: 0 8px 30px rgba(0,0,0,0.6);
      margin-bottom: 18px;
      border-left: 4px solid rgba(0,198,255,0.6);
      display:flex;
      align-items:center;
      gap:20px;
    }
    .hero .title {
      font-size:32px;
      font-weight:800;
      background: linear-gradient(90deg,#75f0ff,#4b6bff);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin:0;
    }
    .hero .tag {
      color:#9fb8d9;
      margin-top:4px;
      font-size:14px;
    }

    /* glass card */
    .glass {
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.06);
      padding:18px;
      border-radius:12px;
      box-shadow: 0 6px 18px rgba(0,0,0,0.45);
    }

    /* input card */
    .input-card {
      padding:14px;
      border-radius:12px;
      background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
      border: 1px solid rgba(255,255,255,0.03);
    }

    /* fancy predict button */
    .predict-btn>button {
      background: linear-gradient(90deg,#00d4ff,#0066ff);
      color:white;
      border-radius:10px;
      padding:10px 22px;
      font-weight:700;
      border: none;
    }

    /* footer */
    footer { color:#9fb8d9; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------
# HERO
# ----------------------------
st.markdown(
    f"""
    <div class="hero">
      <div style="flex:1;">
        <h1 class="title">SmartPay • AI Salary Intelligence</h1>
        <div class="tag">Creative predictive application • LightGBM • FastAPI backend • Streamlit frontend</div>
      </div>
      <div style="width:220px; text-align:right;">
        <img src="https://i.imgur.com/6RMhx.gif" width="180" style="border-radius:12px; box-shadow:0 6px 20px rgba(0,0,0,0.6);" />
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------------------
# layout
# ----------------------------
left, right = st.columns((2, 3))

# ----------------------------
# LEFT: Input / Predict Flow
# ----------------------------
with left:
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.subheader("Enter Candidate Details")
    with st.form("predict_form"):
        st.markdown('<div class="input-card">', unsafe_allow_html=True)
        age = st.number_input("Age", min_value=17, max_value=80, value=28, step=1)
        education = st.selectbox("Education", ["High School", "Bachelor’s", "Master’s", "PhD", "Other"])
        job_title = st.text_input("Job Title", "Software Engineer")
        hours_per_week = st.slider("Hours per week", 10, 100, 40)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        marital_status = st.selectbox("Marital Status", ["Single", "Married", "Divorced", "Other"])
        st.markdown("</div>", unsafe_allow_html=True)

        # extra options
        st.markdown("<hr>", unsafe_allow_html=True)
        with st.expander("Advanced options (optional)"):
            sample_confidence = st.select_slider("Prediction confidence hint", options=["Low", "Medium", "High"], value="High")
            show_confetti = st.checkbox("Celebrate on result (confetti)", value=True)

        # submit at bottom
        submitted = st.form_submit_button(label="🔍 Predict Salary")
    st.markdown("</div>", unsafe_allow_html=True)

    # handle submission (button at bottom)
    if submitted:
        payload = {
            "age": int(age),
            "education": education,
            "job_title": job_title,
            "hours_per_week": int(hours_per_week),
            "gender": gender,
            "marital_status": marital_status
        }

        with st.spinner("Contacting AI engine..."):
            time.sleep(0.8)
            try:
                resp = requests.post(f"{BACKEND_URL}/predict", json=payload, headers=HEADERS, timeout=20)
            except requests.exceptions.RequestException as e:
                st.error(f"Connection error: {e}")
                resp = None

        if resp is None:
            st.markdown("🔌 Could not reach backend. Check backend URL and network.", unsafe_allow_html=True)
        else:
            if resp.status_code == 200:
                data = resp.json()
                salary = float(data.get("predicted_salary_usd", 0))
                # KPI cards
                st.success(f"💰 Predicted annual salary: ${salary:,.2f}", icon="✅")
                if show_confetti:
                    st.balloons()

                # small details + download
                col_a, col_b = st.columns(2)
                col_a.metric("Model", "LightGBM")
                col_b.metric("Confidence", sample_confidence)

                # quick insights (mini chart)
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=salary,
                    title={'text': "Predicted Salary (USD)"},
                    gauge={
                        'axis': {'range': [0, max(1000000, salary * 2)]},
                        'bar': {'color': "#00d4ff"},
                    }
                ))
                st.plotly_chart(fig, use_container_width=True)

                # Downloadable PDF report
                def make_pdf(payload, salary_val):
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", "B", 16)
                    pdf.cell(0, 10, "SmartPay — Salary Prediction Report", ln=True, align="C")
                    pdf.ln(6)
                    pdf.set_font("Arial", size=12)
                    pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
                    pdf.ln(6)
                    pdf.cell(0, 8, "Inputs:", ln=True)
                    for k, v in payload.items():
                        pdf.cell(0, 8, f" - {k}: {v}", ln=True)
                    pdf.ln(6)
                    pdf.cell(0, 8, f"Predicted annual salary (USD): ${salary_val:,.2f}", ln=True)
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                    pdf.output(tmp.name)
                    return tmp.name

                pdf_path = make_pdf(payload, salary)
                with open(pdf_path, "rb") as f:
                    st.download_button("📄 Download report (PDF)", f, file_name="smartpay_report.pdf", mime="application/pdf")
            elif resp.status_code in (401, 403):
                st.error("🔒 Authentication error (401/403). Check API key and backend settings.")
            elif resp.status_code >= 500:
                st.error("🚨 Server error from backend (5xx). Check backend logs.")
            else:
                # show backend message if any
                try:
                    txt = resp.json()
                except Exception:
                    txt = resp.text
                st.error(f"API Error {resp.status_code}: {txt}")

# ----------------------------
# RIGHT: Analysis + Insights
# ----------------------------
with right:
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    tabs = st.tabs(["Live Analysis", "Model Insights", "About & Credits"])

    # ---- Live Analysis
    with tabs[0]:
        st.subheader("Live dataset snapshot & trends")
        try:
            r = requests.get(f"{BACKEND_URL}/analyze", headers=HEADERS, timeout=12)
            if r.status_code == 200:
                summary = r.json().get("summary", {})
                rec = summary.get("record_count", 0)
                avg = summary.get("average_salary", 0.0)
                mx = summary.get("max_salary", 0.0)
                mn = summary.get("min_salary", 0.0)
                c1, c2, c3 = st.columns(3)
                c1.metric("Records", f"{rec:,}")
                c2.metric("Avg Salary", f"${avg:,.2f}")
                c3.metric("Max Salary", f"${mx:,.2f}")

                # simple bar
                df_stats = pd.DataFrame({
                    "label": ["Min", "Avg", "Max"],
                    "value": [mn, avg, mx]
                })
                fig = px.bar(df_stats, x="label", y="value", text="value", color="label",
                             color_discrete_map={"Min":"#ff7b7b","Avg":"#00d4ff","Max":"#7cffb2"})
                fig.update_layout(template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Analysis service not available: " + str(r.status_code))
        except Exception as e:
            st.info("Analysis unavailable: " + str(e))

    # ---- Model Insights
    with tabs[1]:
        st.subheader("Explainability — Top features")
        try:
            r2 = requests.get(f"{BACKEND_URL}/explain", headers=HEADERS, timeout=12)
            if r2.status_code == 200:
                tf = r2.json().get("top_features", [])
                if tf:
                    df = pd.DataFrame(tf)
                    st.dataframe(df, use_container_width=True)
                    fig = px.bar(df, x="feature", y="importance", color="importance", color_continuous_scale="Viridis")
                    fig.update_layout(template="plotly_dark")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No feature info returned.")
            else:
                st.warning("Explainability endpoint returned: " + str(r2.status_code))
        except Exception as e:
            st.info("Explainability unavailable: " + str(e))

    # ---- About
    with tabs[2]:
        st.markdown("#### About SmartPay")
        st.markdown("""
        SmartPay is an AI-driven salary prediction system built with LightGBM (regression).
        This front-end is a creative, product-style demo built in Streamlit.
        """)
        st.write("**Developer:** Yuvaraja P — Final Year CSE (IoT), Paavai Engineering College")
        st.write("**Backend:** FastAPI · LightGBM")
        st.write("**Frontend:** Streamlit · Plotly")
    st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------
# FOOTER
# ----------------------------
st.markdown(
    """
    <div style="position:fixed;right:20px;bottom:14px;background:rgba(255,255,255,0.02);padding:8px 12px;border-radius:12px;border:1px solid rgba(255,255,255,0.04);">
      Developed by <b>Yuvaraja P</b> • Final Year CSE (IoT) • Paavai Engineering College
    </div>
    """,
    unsafe_allow_html=True,
)
