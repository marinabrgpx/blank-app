import streamlit as st
import functions as f
import pandas as pd

add_uploader = st.sidebar.file_uploader("Load Data", type = ["xlsx"])
main = pd.read_excel(add_uploader, sheet_name="actual_model")
st.sidebar.button('View main', on_click=lambda: f.show_main(main), type='tertiary')