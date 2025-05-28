import streamlit as st

home_page = st.Page("home.py", title="Home", icon=":material/home:")

pg = st.navigation([home_page])
st.set_page_config(page_title="Chatbot", page_icon=":material/chat:")
pg.run()
