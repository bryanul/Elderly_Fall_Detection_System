"""Main tracker class combining fall detection and face recognition."""

import threading
import time
from typing import Dict, List, Optional

import numpy as np
from ultralytics import YOLO

from app.core.config import settings
from app.modules.face_recognition import FaceIdentifier
from app.modules.fall_detection import FallDetector
from app.modules.person_tracker import PersonTracker
from app.utils.frame_visualizer import FrameVisualizer
from app.utils.video_processor import VideoProcessor


class FallAndFaceTracker:
    """
    Main tracker class that combines fall detection and face recognition.

    This class orchestrates person tracking, face identification, and fall detection
    in real-time video streams.
    """

    def __init__(
        self,
        yolo_person_path: str,
        face_db: Optional[Dict[str, List[float]]],
        video_source,
        fall_conf: float = 0.6,
        face_conf: float = 0.3,
        face_id_threshold: float = 1.22,
        fall_class_idx: int = 1,
        threshold_fall_frames: int = 3,
        alert_bot=None,
    ):
        """
        Initialize the fall and face tracker.

        Args:
            yolo_person_path: Path to YOLO model for person detection
            face_db: Dictionary mapping names to face embeddings
            video_source: Video source (camera index or file path)
            fall_conf: Confidence threshold for fall detection
            face_conf: Confidence threshold for face detection
            face_id_threshold: Distance threshold for face identification
            fall_class_idx: Class index for fall detection in YOLO model
            threshold_fall_frames: Number of consecutive frames to confirm a fall
            alert_bot: Optional alert bot for sending notifications
        """
        # Core models and data
        self.person_model = YOLO(yolo_person_path)
        self.fall_threshold = fall_conf
        self.conf_threshold = face_conf
        self.alert_bot = alert_bot
        self.running = False

        # Initialize components
        self.face_identifier = FaceIdentifier(face_db, face_id_threshold)
        self.fall_detector = FallDetector(fall_class_idx, threshold_fall_frames)
        self.person_tracker = PersonTracker()
        self.video_processor = VideoProcessor(video_source)
        self.visualizer = FrameVisualizer()

    def process_person_detection(self, frame: np.ndarray, det) -> None:
        """
        Process a single person detection.

        Args:
            frame: Current video frame
            det: Detection object from YOLO
        """
        x1, y1, x2, y2 = map(int, det.xyxy[0])
        class_id = int(det.cls[0]) if hasattr(det, "cls") else 0
        class_name = (
            self.person_model.names[class_id]
            if hasattr(self.person_model, "names")
            else str(class_id)
        )
        track_id = int(det.id[0]) if det.id is not None else None

        if track_id is None:
            self.visualizer.draw_person_box(
                frame, (x1, y1, x2, y2), class_name=class_name
            )
            return

        # Process fall detection
        if self.fall_detector.process_detection(track_id, class_id):
            identity = self.person_tracker.get_identity(track_id) or "Alguien"
            identity_text = f"{identity} ha sufrido una caída!"
            self.send_alert_bot("Caída detectada!", identity_text)

        # Handle face identification
        if self.person_tracker.has_identity(track_id):
            identity = self.person_tracker.get_identity(track_id)
            self.visualizer.draw_person_box(
                frame, (x1, y1, x2, y2), track_id, identity, class_name
            )
            return

        # Attempt face identification if needed
        if not self.person_tracker.should_attempt_identification(track_id):
            identity = self.person_tracker.get_identity(track_id)
            self.visualizer.draw_person_box(
                frame, (x1, y1, x2, y2), track_id, identity, class_name
            )
            return

        # Extract face and identify
        person_crop = frame[y1:y2, x1:x2]
        identity = self.face_identifier.extract_and_identify_face(person_crop)

        if identity is not None:
            self.person_tracker.set_identity(track_id, identity)
        else:
            self.person_tracker.increment_attempt(track_id)

        # Draw visualization
        current_identity = self.person_tracker.get_identity(track_id)
        self.visualizer.draw_person_box(
            frame, (x1, y1, x2, y2), track_id, current_identity, class_name
        )

    def process_video(self) -> None:
        """Main video processing loop."""
        # Wait for face database to be available
        while (
            self.face_identifier.face_db is None
            or len(self.face_identifier.face_db) == 0
        ):
            time.sleep(1)

        # Set up video capture
        cap, frame_interval, display_size = self.video_processor.setup_capture()
        frame_count = 0
        self.running = True

        try:
            while cap.isOpened() and self.running:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_count += 1
                if frame_count % frame_interval != 0:
                    continue

                # Run person detection and tracking
                person_results = self.person_model.track(
                    frame,
                    conf=self.fall_threshold,
                    persist=True,
                    tracker=settings.model.tracking_config_path,
                    device=settings.model.device,
                    agnostic_nms=True,
                )

                # Process each detection
                for det in person_results[0].boxes:
                    self.process_person_detection(frame, det)

                # Update latest frame for streaming
                self.video_processor.update_latest_frame(frame, display_size)
                frame_count = 0

        finally:
            cap.release()

    def start_async(self) -> None:
        """Start video processing in a separate thread."""
        t = threading.Thread(target=self.process_video, daemon=True)
        t.start()

    def get_latest_frame(self) -> Optional[bytes]:
        """
        Get the latest processed frame as bytes.

        Returns:
            Latest frame as JPEG bytes or None if no frame available
        """
        return self.video_processor.get_latest_frame_bytes()

    def send_alert_bot(self, alert_title: str, alert_message: str) -> None:
        """
        Send an alert through the configured alert bot.

        Args:
            alert_title: Title of the alert
            alert_message: Alert message content
        """
        if self.alert_bot is not None:
            image_base64 = self.video_processor.get_latest_frame_base64()
            if image_base64:
                self.alert_bot.send_alert(
                    alert_title, alert_message, image_base64, "Emergencia"
                )

    def set_face_db(self, emb_dict: Dict[str, List[float]]) -> None:
        """
        Update the face database.

        Args:
            emb_dict: Dictionary mapping names to face embeddings
        """
        self.face_identifier.face_db = emb_dict
