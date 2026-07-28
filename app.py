"""Streamlit operator dashboard (optional).  streamlit run app.py

Read-only local UI: synthetic scenarios or uploaded canonical CSV.
Never actuates equipment; never writes to SCADA.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import streamlit as st
import pandas as pd
from wellguard.generator import generate, SCENARIOS
from wellguard.physics import physics_features
from wellguard.pipeline import run

MAX_UPLOAD_BYTES = 25 * 1024 * 1024

st.set_page_config(page_title="WellGuard OS", layout="wide")
st.title("WellGuard OS — advisory ESP well surveillance")
st.caption(
    "Research demonstrator. Advisory only. Never actuates equipment. "
    "Карточка — повод для проверки, не диагноз отказа/аварии. "
    "Метрики на синтетике ≠ полевая точность."
)

col = st.sidebar
source = col.radio("Источник", ["Синтетический сценарий", "CSV телеметрии"], index=0)

if source == "Синтетический сценарий":
    scenario = col.selectbox("Scenario", SCENARIOS, index=1)
    seed = col.number_input("Seed", 0, 999, 0)
    df = generate(scenario, seed=int(seed))
else:
    uploaded = col.file_uploader("Canonical CSV", type=["csv"])
    if uploaded is None:
        st.info("Загрузите CSV с каноническими каналами (см. docs / GPN contract).")
        st.stop()
    raw = uploaded.getvalue()
    if len(raw) > MAX_UPLOAD_BYTES:
        st.error("Файл слишком большой (max 25 MiB).")
        st.stop()
    df = pd.read_csv(uploaded)
    if df.empty:
        st.error("Пустой CSV.")
        st.stop()

card = run(df)

c1, c2 = st.columns([2, 1])
with c1:
    plot_cols = [c for c in ["intake_p_bar", "current_a", "q_liq_m3d"] if c in df.columns]
    if plot_cols and "t_min" in df.columns:
        st.line_chart(df.set_index("t_min")[plot_cols])
    try:
        f = physics_features(df)
        feat_cols = [c for c in ["head_coef", "current_var"] if c in f.columns]
        if feat_cols and "t_min" in f.columns:
            st.line_chart(f.set_index("t_min")[feat_cols])
    except Exception as e:
        st.warning(f"Physics features unavailable: {e}")
with c2:
    st.subheader("Operator card")
    st.json(card)
    st.caption(card.get("output_limits", ""))
