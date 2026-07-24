"""Streamlit operator dashboard (optional).  streamlit run app.py"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import streamlit as st
import pandas as pd
from wellguard.generator import generate, SCENARIOS
from wellguard.physics import physics_features
from wellguard.pipeline import run

st.set_page_config(page_title="WellGuard OS", layout="wide")
st.title("WellGuard OS — advisory ESP well surveillance")
st.caption("Research demonstrator. Advisory only. Never actuates equipment.")

col = st.sidebar
scenario = col.selectbox("Scenario", SCENARIOS, index=1)
seed = col.number_input("Seed", 0, 999, 0)
df = generate(scenario, seed=int(seed))
card = run(df)

c1, c2 = st.columns([2, 1])
with c1:
    f = physics_features(df)
    st.line_chart(df.set_index("t_min")[["intake_p_bar", "current_a", "q_liq_m3d"]])
    st.line_chart(f.set_index("t_min")[["head_coef", "current_var"]])
with c2:
    st.subheader("Operator card")
    st.json(card)
