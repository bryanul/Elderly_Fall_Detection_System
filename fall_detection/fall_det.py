import cv2
import numpy as np
from ultralytics import YOLO
from deepface import DeepFace
import time
class FallAndFaceTracker:
    def __init__(self, yolo_person_path, face_db, fall_conf=0.3, face_conf=0.3, face_id_threshold=0.5, fall_class_idx=1, threshold_fall_frames=5):
        self.person_model = YOLO(yolo_person_path)
        self.face_db = face_db  # dict: {name: embedding}
        self.fall_threshold = fall_conf
        self.conf_threshold = face_conf
        self.track_id_to_identity = {}
        self.face_id_threshold = face_id_threshold
        self.track_id_attempts = {}
        self.track_id_last_attempt = {}
        self.consecutive_fall_frames = {}
        self.fall_class_idx = fall_class_idx
        self.threshold_fall_frames = threshold_fall_frames
        self.fall_reported_ids = set()

    def identify_face(self, embedding):
        min_dist = float('inf')
        identity = None
        for name, db_emb in self.face_db.items():
            dist = np.linalg.norm(embedding - db_emb)
            if dist < min_dist and dist < self.face_id_threshold:
                min_dist = dist
                identity = name
        return identity

    def start(self, rtsp_url):
        try:
            cap = cv2.VideoCapture(rtsp_url)
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            display_width = 1600
            scale = display_width / width
            new_height = int(height * scale)
            frame_interval = max(1, int(fps // 10))  # Adjust divisor as needed
            frame_count = 0

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    print("Failed to read frame from RTSP stream.")
                    break
                frame_count += 1
                if frame_count % frame_interval != 0:
                    continue
                person_results = self.person_model.track(frame, conf=self.fall_threshold, persist=True, tracker='botsort.yaml')
                for det in person_results[0].boxes:
                    x1, y1, x2, y2 = map(int, det.xyxy[0])
                    class_id = int(det.cls[0]) if hasattr(det, 'cls') else 0
                    class_name = self.person_model.names[class_id] if hasattr(self.person_model, 'names') else str(class_id)
                    track_id = int(det.id[0]) if det.id is not None else None

                    if track_id is not None:
                        # Check if this detection is a fall
                        if class_id == self.fall_class_idx:  # Set fall_class_idx to the correct class index for 'fall'
                            self.consecutive_fall_frames[track_id] = self.consecutive_fall_frames.get(track_id, 0) + 1
                            if self.consecutive_fall_frames[track_id] >= self.threshold_fall_frames:
                                if track_id not in self.fall_reported_ids:
                                    identity = self.track_id_to_identity.get(track_id, "unknown")
                                    print(f"Fall detected! Identity: {identity}, ID: {track_id}, Status: Fall")
                                    self.fall_reported_ids.add(track_id)
                                self.consecutive_fall_frames[track_id] = 0
                        else:
                            self.consecutive_fall_frames[track_id] = 0
                            if track_id in self.fall_reported_ids:
                                self.fall_reported_ids.remove(track_id)

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)

                    if track_id is not None and track_id in self.track_id_to_identity:
                        identity = self.track_id_to_identity[track_id]
                        cv2.putText(frame, f"{identity} (ID:{track_id}), {class_name}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                                    (0, 255, 0), 2)
                        continue # Skip face detection for this track_id

                    # Detect face in person box
                    if track_id is not None:
                        now = time.time()
                        last = self.track_id_last_attempt.get(track_id, 0)
                        if now - last > 1:  # 1 second interval
                            self.track_id_attempts[track_id] = 0
                        self.track_id_last_attempt[track_id] = now
                        if self.track_id_attempts[track_id] >= 5:
                            self.track_id_to_identity[track_id] = "no id"
                            cv2.putText(frame, f"no id (ID:{track_id})", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                                        (0, 0, 255), 2)
                            continue
                    print(f"Processing track ID: {track_id} at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
                    person_crop = frame[y1:y2, x1:x2]
                    embedding = DeepFace.represent(person_crop, model_name='VGG-Face', detector_backend = 'yolov11n', enforce_detection=False, align=True)[0]["embedding"]
                    identity = self.identify_face(embedding)
                    if identity is not None and track_id is not None:
                        self.track_id_to_identity[track_id] = identity
                        self.track_id_attempts.pop(track_id, None)  # Reset attempts
                        cv2.putText(frame, f"{identity} (ID:{track_id})", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                                    (0, 255, 0), 2)
                    elif track_id is not None:
                        self.track_id_attempts[track_id] += 1
                frame = cv2.resize(frame, (display_width, new_height))
                cv2.imshow('RTSP Fall & Face Tracker', frame)
                frame_count = 0
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            cap.release()
            cv2.destroyAllWindows()
        except Exception as e:
            print(f"Error processing: {e}")

if __name__ == "__main__":
    yolo_person_path = "./models/yolo11s-final.pt"  # Update with your YOLO model path
    face_db = {}  # Load or define your face embeddings database here
    #"C:\\Users\\bryan\\Downloads\\IMG_0578.MOV"
    rtsp_url = "C:\\Users\\bryan\\Downloads\\IMG_0578.MOV"  # Update with your RTSP stream URL
    fall_class_idx = 1  # Set this to your 'fall' class index
    threshold = 5
    tracker = FallAndFaceTracker(yolo_person_path, face_db, fall_class_idx=fall_class_idx, threshold_fall_frames=threshold)
    tracker.start(rtsp_url)