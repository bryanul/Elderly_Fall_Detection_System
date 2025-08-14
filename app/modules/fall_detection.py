"""Fall detection and tracking logic."""

from typing import Dict, Set


class FallDetector:
    """Handles fall detection logic for tracked persons."""

    def __init__(self, fall_class_idx: int = 1, threshold_frames: int = 3):
        """
        Initialize fall detector.

        Args:
            fall_class_idx: Class index for fall detection in YOLO model
            threshold_frames: Number of consecutive frames to confirm a fall
        """
        self.fall_class_idx = fall_class_idx
        self.threshold_frames = threshold_frames
        self.consecutive_fall_frames: Dict[int, int] = {}
        self.fall_reported_ids: Set[int] = set()

    def process_detection(self, track_id: int, class_id: int) -> bool:
        """
        Process a detection for fall analysis.

        Args:
            track_id: Tracking ID of the person
            class_id: Detected class ID

        Returns:
            True if a new fall is detected, False otherwise
        """
        if class_id == self.fall_class_idx:
            self.consecutive_fall_frames[track_id] = (
                self.consecutive_fall_frames.get(track_id, 0) + 1
            )
            if (
                self.consecutive_fall_frames[track_id] >= self.threshold_frames
                and track_id not in self.fall_reported_ids
            ):
                self.fall_reported_ids.add(track_id)
                self.consecutive_fall_frames[track_id] = 0
                return True
        else:
            self.consecutive_fall_frames[track_id] = 0
            if track_id in self.fall_reported_ids:
                self.fall_reported_ids.remove(track_id)

        return False
