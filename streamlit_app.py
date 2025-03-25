import streamlit as st
import functions as f
import pandas as pd

uploaded_file = st.sidebar.file_uploader("Load Data", type = ["xlsx"])
df = pd.read_excel(uploaded_file, sheet_name="actual_model")
st.dataframe(df, use_container_width=True)