import os
import cv2
import numpy as np
import streamlit as st
from ultralytics import YOLO
from deepface import DeepFace
from scipy.spatial.distance import cosine
from datetime import datetime


# ============================
# Embedding Database
# ============================

class EmbeddingDatabase:
    def __init__(self, db_path, model_name="Facenet512"):
        self.db_path = db_path
        self.model_name = model_name
        self.embeddings = {}

    def build_database(self):
        self.embeddings = {}

        if not os.path.exists(self.db_path):
            os.makedirs(self.db_path)

        for person in os.listdir(self.db_path):
            person_dir = os.path.join(self.db_path, person)
            if not os.path.isdir(person_dir):
                continue

            self.embeddings[person] = []

            for img in os.listdir(person_dir):
                img_path = os.path.join(person_dir, img)
                emb = DeepFace.represent(
                    img_path=img_path,
                    model_name=self.model_name,
                    detector_backend="retinaface",
                    enforce_detection=False
                )[0]["embedding"]

                self.embeddings[person].append(np.array(emb))

        print("✅ Embedding database ready")

    def add_person(self, name, image_paths):
        if name not in self.embeddings:
            self.embeddings[name] = []

        person_dir = os.path.join(self.db_path, name)
        os.makedirs(person_dir, exist_ok=True)

        for img_path in image_paths:
            filename = os.path.basename(img_path)
            save_path = os.path.join(person_dir, filename)
            cv2.imwrite(save_path, cv2.imread(img_path))

            emb = DeepFace.represent(
                img_path=save_path,
                model_name=self.model_name,
                detector_backend="retinaface",
                enforce_detection=False
            )[0]["embedding"]

            self.embeddings[name].append(np.array(emb))


# ============================
# Face Recognizer
# ============================

class FaceRecognizer:
    def __init__(self, embedding_db, distance_threshold=0.35):
        self.embedding_db = embedding_db
        self.distance_threshold = distance_threshold

    def recognize(self, face_img):
        try:
            rep = DeepFace.represent(
                img_path=face_img,
                model_name="Facenet512",
                detector_backend="retinaface",
                enforce_detection=False
            )
        except:
            return "Unknown", 0.0

        query_emb = np.array(rep[0]["embedding"])

        best_name = "Unknown"
        best_distance = 1.0

        for name, embeddings in self.embedding_db.embeddings.items():
            for db_emb in embeddings:
                dist = cosine(query_emb, db_emb)
                if dist < best_distance:
                    best_distance = dist
                    best_name = name

        confidence = (1 - best_distance) * 100

        if best_distance <= self.distance_threshold:
            return best_name, confidence
        else:
            return "Unknown", confidence


# ============================
# Surveillance Engine
# ============================

class SurveillanceEngine:
    def __init__(self, frame_skip=5, db_path="database"):
        self.model = YOLO("yolov8n.pt")
        self.frame_skip = frame_skip

        self.embedding_db = EmbeddingDatabase(db_path)
        self.embedding_db.build_database()

        self.face_recognizer = FaceRecognizer(self.embedding_db)

        self.track_status = {}
        self.intruder_ids = set()
        self.frame_count = 0

    def point_in_roi(self, cx, cy, roi_points):
        roi_np = np.array(roi_points, np.int32)
        return cv2.pointPolygonTest(roi_np, (cx, cy), False) >= 0

    def process_frame(self, frame):
        self.frame_count += 1

        results = self.model.track(
            frame,
            persist=True,
            tracker="bytetrack.yaml",
            classes=[0],
            verbose=False
        )

        if results[0].boxes is None or results[0].boxes.id is None:
            return frame

        for box in results[0].boxes:
            track_id = int(box.id[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)

            label = "OUTSIDE ROI"
            color = (255, 255, 0)

            for zone in st.session_state.rois:
                if not zone.get("active", True):
                    continue

                if self.point_in_roi(cx, cy, zone["points"]):

                    if track_id not in self.track_status:
                        self.track_status[track_id] = {"status": "PENDING", "name": ""}

                    if self.frame_count % self.frame_skip == 0 and self.track_status[track_id]["status"] == "PENDING":
                        person_crop = frame[y1:y2, x1:x2]
                        name, confidence = self.face_recognizer.recognize(person_crop)

                        if name != "Unknown":
                            self.track_status[track_id] = {"status": "AUTHORIZED", "name": name}
                        else:
                            self.track_status[track_id] = {"status": "INTRUDER", "name": "Unknown"}

                            if track_id not in self.intruder_ids:
                                self.intruder_ids.add(track_id)
                                self.log_alert(zone["name"], "Unknown")

                    status = self.track_status[track_id]["status"]
                    name = self.track_status[track_id]["name"]

                    if status == "AUTHORIZED":
                        label = f"{name}"
                        color = (0, 255, 0)
                    elif status == "INTRUDER":
                        label = "INTRUDER"
                        color = (0, 0, 255)
                    else:
                        label = "SCANNING..."
                        color = (255, 255, 0)

            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        return frame

    def log_alert(self, zone_name, person_name):
        alert = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "zone": zone_name,
            "person": person_name
        }
        st.session_state.alerts.append(alert)

    def add_new_person(self, name, image_paths):
        self.embedding_db.add_person(name, image_paths)
        print(f"✅ Added {name} to database")