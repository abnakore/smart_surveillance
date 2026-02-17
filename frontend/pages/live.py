import streamlit as st
import cv2
import numpy as np
import time
from utils.video_utils import load_video_frames
# from components.alert_panel import show_alerts

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

    for frame in load_video_frames(video_source):
        if not st.session_state.processing:
            break

        # Draw active zones
        for zone in st.session_state.rois:
            if not zone.get("active", True):
                continue
            json_data = zone.get("json_data")
            if not json_data or "objects" not in json_data:
                continue

            for obj in json_data["objects"]:
                if obj.get("type") in ("polygon", "path"):
                    path = obj.get("path", [])
                    points = []
                    for cmd in path:
                        if len(cmd) >= 3:  # ['M', x, y] or ['L', x, y]
                            points.append([cmd[1], cmd[2]])
                    if not points:
                        continue

                    # Use points directly, since json_data is in original video coordinates
                    pts = np.array(points, np.int32)
                    pts = pts.reshape((-1, 1, 2))
                    color = zone.get("color", (0, 255, 0))
                    cv2.polylines(frame, [pts], isClosed=True, color=color, thickness=2)

        # Convert BGR -> RGB for Streamlit
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        video_placeholder.image(frame_rgb, channels="RGB", use_column_width=True)

        # Control frame rate (approx. 30 FPS)
        time.sleep(0.06)

    # Processing finished
    st.session_state.processing = False
    st.rerun()

elif not st.session_state.get("video_source"):
    st.info("Please upload a video in the Settings page first.")