import streamlit as st
import cv2
import numpy as np
import time
from utils.video_utils import load_video_frames
# from components.alert_panel import show_alerts

from backend.surveillance_engine import SurveillanceEngine
import cv2

# Initialize Surveillance Engine
if "engine" not in st.session_state:
    st.session_state.engine = SurveillanceEngine(frame_skip=5, db_path="database")

if "alerts" not in st.session_state:
    st.session_state.alerts = []

# ------------------------------
# Constants
# ------------------------------
MAX_CANVAS_WIDTH = 1200

# ------------------------------
# Page Layout
# ------------------------------
st.subheader("Live Video Feed")

col_video, col_alerts = st.columns([2, 1])

with col_video:
    video_placeholder = st.empty()
    video_placeholder.info("Video feed will appear here once processing starts.")

    # Start / Stop buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start Processing", key="start_live"):
            st.session_state.processing = True
    with col2:
        if st.button("Stop Processing", key="stop_live"):
            st.session_state.processing = False

with col_alerts:
    st.subheader("Alerts")
    alert_container = st.container()
    with alert_container:
        if st.session_state.alerts:
            for alert in reversed(st.session_state.alerts[-5:]):
                st.warning(f"{alert['time']} - {alert['zone']} - {alert['person']}")
        else:
            st.caption("No alerts yet.")

    if st.button("Clear Alerts", key="clear_alerts"):
        st.session_state.alerts = []
        st.rerun()

# ------------------------------
# Video Processing Loop
# ------------------------------
if st.session_state.get("processing") and st.session_state.get("video_source"):
    video_source = st.session_state.video_source

    # Get original video dimensions
    cap = cv2.VideoCapture(video_source)
    orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()

    # Compute scaling factor used during drawing
    scale = min(1.0, MAX_CANVAS_WIDTH / orig_w) if orig_w > 0 else 1.0

    engine = st.session_state.engine
    cap = cv2.VideoCapture(st.session_state.video_source)

    while st.session_state.processing:
        ret, frame = cap.read()
        if not ret:
            break

        processed_frame = engine.process_frame(frame)

        frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
        video_placeholder.image(frame_rgb, channels="RGB", use_column_width=True)

    cap.release()

    st.session_state.processing = False
    st.rerun()
    # Processing finished
    st.session_state.processing = False
    st.rerun()

elif not st.session_state.get("video_source"):
    st.info("Please upload a video in the Settings page first.")