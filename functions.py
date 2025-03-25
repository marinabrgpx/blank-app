import streamlit as st
import pandas as pd

def show_main(df):
    st.dataframe(df)