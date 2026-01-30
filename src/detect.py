"""
detect.py
Detecta espermatozoides em cada frame usando YOLOv8 (Ultralytics).
Retorna lista de detecções: [frame_id, x1, y1, x2, y2, score]
"""

from ultralytics import YOLO
import cv2
import numpy as np

class SpermDetector:
    def __init__(self, weights="models/yolo/yolov8n.pt", conf=0.25, device=None):
        self.model = YOLO(weights)
        self.conf = conf

    def detect_video(self, video_path, max_frames=None, skip_frames=0):
        cap = cv2.VideoCapture(video_path)
        detections = []
        frame_id = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if skip_frames > 0 and (frame_id % (skip_frames + 1)) != 0:
                frame_id += 1
                continue

            results = self.model(frame, conf=self.conf, verbose=False)
            if len(results) == 0:
                frame_id += 1
                continue
            r = results[0]
            for box in r.boxes:
                try:
                    xyxy = box.xyxy[0].cpu().numpy()  # [x1, y1, x2, y2]
                    score = float(box.conf[0].cpu().numpy())
                except Exception:
                    # fallback: boxes as numpy
                    xyxy = box.xyxy[0].numpy()
                    score = float(box.conf[0].numpy())
                x1, y1, x2, y2 = xyxy.tolist()
                detections.append([frame_id, float(x1), float(y1), float(x2), float(y2), score])
            frame_id += 1
            if max_frames and frame_id >= max_frames:
                break
        cap.release()
        return detections