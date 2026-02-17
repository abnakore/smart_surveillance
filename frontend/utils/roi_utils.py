import streamlit as st
from datetime import datetime

def color_from_id(zone_id: int) -> tuple:
    # Simple deterministic RGB generator from ID
    r = (zone_id * 73) % 256
    g = (zone_id * 151) % 256
    b = (zone_id * 199) % 256
    return (b, g, r)  # OpenCV uses BGR

def add_mock_alert():
    """Add a mock alert for testing."""
    st.session_state.alerts.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "zone": "Server Room",
        "person": "Unknown"
    })