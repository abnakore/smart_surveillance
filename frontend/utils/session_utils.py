import streamlit as st
from datetime import datetime

def init_session_state():
    """Initialise all persistent variables."""
    defaults = {
        "rois": [],               # list of dicts: {name, points, color, active}
        "authorized_faces": [],   # list of dicts: {name, encoding (None for mock)}
        "alerts": [],             # list of dicts: {time, zone, person}
        "video_source": None,     # "upload" or "webcam"
        "processing": False,      # whether video is playing
        "canvas_background": None,# current frame for drawing
        "canvas_background_rgb": None,
        "original_frame_bgr": None,
        "show_canvas": False,     # whether to show drawing canvas
        "editing_roi_index": None,# index of ROI being edited
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
