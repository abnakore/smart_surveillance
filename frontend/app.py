import streamlit as st
from utils.session_utils import init_session_state

# Initialise session state (runs once at startup)
init_session_state()

st.set_page_config(layout="wide")

st.title("Selective Smart Surveillance Control Room")
st.markdown("""
This dashboard allows you to:
- Monitor live video feeds
- Define restricted zones (polygons)
- Manage authorised personnel
- Receive real-time alerts when unauthorised entry occurs

Use the sidebar to navigate between the Live Stream and Settings pages.
""")