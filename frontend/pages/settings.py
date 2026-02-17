import streamlit as st
import cv2
import pandas as pd
from PIL import Image
from streamlit_drawable_canvas import st_canvas

from utils.video_utils import extract_first_frame
from utils.roi_utils import  add_mock_alert, color_from_id
import json
from copy import deepcopy

st.subheader("Settings")

# ------------------------------
# 1. Video Source
# ------------------------------
st.markdown("### Video Source")
source = st.radio("Select source", ["Upload video", "Webcam"], key="source_radio")
if source == "Upload video":
    uploaded_file = st.file_uploader("Choose a video file", type=["mp4", "avi", "mov", "mkv"])
    if uploaded_file:
        temp_path = f"/tmp/{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.read())
        st.session_state.video_source = temp_path
        st.success(f"File ready: {uploaded_file.name}")
    else:
        st.info("Upload a video to begin.")
else:
    st.info("Webcam support can be added later with streamlit-webrtc.")

st.divider()

# ------------------------------
# 2. Restricted Zones
# ------------------------------
st.markdown("### Restricted Zones")

if st.session_state.get("video_source"):
    # Extract first frame for drawing
    frame = extract_first_frame(st.session_state.video_source)
    if frame is not None:
        # Store original BGR frame and also RGB for canvas
        st.session_state.original_frame_bgr = frame
        st.session_state.canvas_background_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    else:
        st.error("Could not read first frame.")

    if st.session_state.get("canvas_background_rgb") is not None:
        # Determine scaling factor to fit canvas in UI
        max_canvas_width = 700
        orig_h, orig_w = st.session_state.canvas_background_rgb.shape[:2]
        scale = min(1.0, max_canvas_width / orig_w)
        canvas_w = int(orig_w * scale)
        canvas_h = int(orig_h * scale)

        # Resize the background image for display
        pil_image = Image.fromarray(st.session_state.canvas_background_rgb)
        pil_image_resized = pil_image.resize((canvas_w, canvas_h), Image.Resampling.LANCZOS)

        if st.button("Draw New Zone"):
            st.session_state.show_canvas = True
            st.session_state.editing_roi_index = None
            # st.rerun()

        if st.session_state.get("show_canvas", False):
            # Prepare initial drawing (scale existing ROI points if editing)
            initial_drawing = None
            if st.session_state.editing_roi_index is not None:
                roi = st.session_state.rois[st.session_state.editing_roi_index]
                json_for_canvas = deepcopy(roi["json_data"])
                for obj in json_for_canvas["objects"]:
                    if "path" in obj:
                        for cmd in obj["path"]:
                            if cmd[0] in ["M","L"]:
                                cmd[1] = int(cmd[1] * scale)
                                cmd[2] = int(cmd[2] * scale)
                    # Scale object metadata
                    for key in ["left", "top", "width", "height"]:
                        if key in obj and obj[key] is not None:
                            obj[key] = obj[key] * scale

                initial_drawing = json_for_canvas
                zone_id = roi["id"]  # use existing ID for color
            else:
                # Determine new zone ID
                if st.session_state.rois:
                    zone_id = max(zone["id"] for zone in st.session_state.rois) + 1
                else:
                    zone_id = 1

            # Get color for the zone
            zone_color = color_from_id(zone_id)  # returns (B,G,R)

            canvas_result = st_canvas(
                fill_color=f"rgba({zone_color[2]}, {zone_color[1]}, {zone_color[0]}, 0.1)",
                stroke_width=2,
                stroke_color=f"rgb({zone_color[2]}, {zone_color[1]}, {zone_color[0]})",
                background_image=pil_image_resized,
                # update_streamlit=True,
                height=canvas_h,
                width=canvas_w,
                drawing_mode="polygon",
                key=f"roi_canvas",
                initial_drawing=initial_drawing
            )

            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.button("Save Zone"):
                    if canvas_result.json_data is not None:
                        objects = pd.json_normalize(canvas_result.json_data["objects"])
                        print("JSON DATA: ", json.dumps(canvas_result.json_data))

                        # Convert all paths to original video coordinates
                        canvas_result_json = deepcopy(canvas_result.json_data)
                        for obj in canvas_result_json["objects"]:
                            if "path" in obj:
                                for cmd in obj["path"]:
                                    if cmd[0] in ["M","L"]:  # only scale M/L commands
                                        cmd[1] = int(cmd[1] / scale)
                                        cmd[2] = int(cmd[2] / scale)
                            # Also scale object metadata
                            for key in ["left", "top", "width", "height"]:
                                if key in obj and obj[key] is not None:
                                    obj[key] = obj[key] / scale


                        polygons = objects[objects['type'].isin(['polygon', 'path'])]
                        if not polygons.empty:
                            poly = polygons.iloc[0]
                            points = poly['path']
                            coords_scaled = []
                            for pt in points:
                                if len(pt) >= 3:
                                    coords_scaled.append([pt[1], pt[2]])
                            if coords_scaled:
                                # Scale back to original coordinates
                                coords_original = [[int(x / scale), int(y / scale)] for (x, y) in coords_scaled]

                                if st.session_state.editing_roi_index is not None:
                                    zone_id = st.session_state.rois[st.session_state.editing_roi_index]["id"]
                                else:
                                    # Recompute ID in case new zones were added while canvas was open
                                    if st.session_state.rois:
                                        zone_id = max(zone["id"] for zone in st.session_state.rois) + 1
                                    else:
                                        zone_id = 1

                                new_roi = {
                                    "id": zone_id,
                                    "name": f"Zone {zone_id}",
                                    "points": coords_original,
                                    "color": color_from_id(zone_id),
                                    "json_data": canvas_result_json,
                                    "active": True
                                }

                                if st.session_state.editing_roi_index is not None:
                                    st.session_state.rois[st.session_state.editing_roi_index] = new_roi
                                else:
                                    st.session_state.rois.append(new_roi)

                    st.session_state.show_canvas = False
                    st.session_state.editing_roi_index = None
                    st.rerun()

            with col_cancel:
                if st.button("Cancel"):
                    st.session_state.show_canvas = False
                    st.session_state.editing_roi_index = None
                    st.rerun()

        # List existing zones
        if st.session_state.rois:
            st.markdown("**Saved Zones**")
            for i, zone in enumerate(st.session_state.rois):
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                col1.write(zone.get("name", f"Zone {i+1}"))

                toggle_label = "Disable" if zone.get("active", True) else "Enable"
                if col2.button(toggle_label, key=f"toggle_{i}"):
                    st.session_state.rois[i]['active'] = not zone.get("active", True)
                    st.rerun()
                    
                if col3.button("Edit", key=f"edit_{i}"):
                    st.session_state.show_canvas = True
                    st.session_state.editing_roi_index = i
                    st.rerun()

                if col4.button("Delete", key=f"del_{i}"):
                    st.session_state.rois.pop(i)
                    st.rerun()
        else:
            st.caption("No zones defined yet.")
    else:
        st.info("Upload a video first to see the first frame and draw zones.")
else:
    st.info("Upload a video first to see the first frame and draw zones.")

st.divider()

# ------------------------------
# 3. Authorised Personnel
# ------------------------------
st.markdown("### Authorised Personnel")
uploaded_face = st.file_uploader("Upload face image", type=["jpg", "jpeg", "png"], key="face_upload")
if uploaded_face:
    name = st.text_input("Name", key="auth_name")
    if st.button("Add Person", key="add_auth"):
        st.session_state.authorized_faces.append({"name": name, "encoding": None})
        st.success(f"{name} added (mock).")
        st.rerun()

if st.session_state.authorized_faces:
    for i, person in enumerate(st.session_state.authorized_faces):
        col1, col2 = st.columns([4, 1])
        col1.write(f"{person['name']}")
        if col2.button("Remove", key=f"remove_auth_{i}"):
            st.session_state.authorized_faces.pop(i)
            st.rerun()
else:
    st.caption("No authorised persons added.")

st.divider()

# ------------------------------
# 4. Mock Data
# ------------------------------
st.markdown("### Mock Data")
col1, col2 = st.columns(2)

with col2:
    if st.button("Add Mock Alert"):
        add_mock_alert()
        # st.rerun()