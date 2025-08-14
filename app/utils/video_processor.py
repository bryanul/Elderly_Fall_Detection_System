"""Video processing and frame management."""

import base64
from typing import Optional, Tuple

import cv2
import numpy as np


class VideoProcessor:
    """Handles video capture and frame processing."""

    def __init__(self, video_source, display_width: int = 800):
        """
        Initialize video processor.

        Args:
            video_source: Video source (camera index or file path)
            display_width: Width for display scaling
        """
        self.video_source = video_source
        self.display_width = display_width
        self.latest_frame: Optional[np.ndarray] = None

    def setup_capture(self) -> Tuple[cv2.VideoCapture, int, Tuple[int, int]]:
        """
        Set up video capture and calculate frame parameters.

        Returns:
            Tuple of (capture object, frame interval, display dimensions)
        """
        cap = cv2.VideoCapture(self.video_source)
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        scale = self.display_width / width if width else 1
        new_height = int(height * scale) if height else 600
        frame_interval = max(1, int(fps // 10)) if fps else 1

        return cap, frame_interval, (self.display_width, new_height)

    def update_latest_frame(
        self, frame: np.ndarray, display_size: Tuple[int, int]
    ) -> None:
        """Update the latest frame for streaming."""
        resized_frame = cv2.resize(frame, display_size)
        self.latest_frame = resized_frame

    def get_latest_frame_bytes(self) -> Optional[bytes]:
        """
        Get the latest frame as bytes for streaming.

        Returns:
            Frame as JPEG bytes or None if no frame available
        """
        if self.latest_frame is None:
            return None
        ret, buffer = cv2.imencode(".jpg", self.latest_frame)
        return buffer.tobytes()

    def get_latest_frame_base64(self) -> Optional[str]:
        """
        Get the latest frame as base64 string.

        Returns:
            Frame as base64 string or None if no frame available
        """
        frame_bytes = self.get_latest_frame_bytes()
        if frame_bytes is None:
            return None
        return base64.b64encode(frame_bytes).decode("utf-8")
