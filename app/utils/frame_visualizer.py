"""Visualization utilities for drawing on frames."""

from typing import Optional

import cv2
import numpy as np


class FrameVisualizer:
    """Handles drawing detections and labels on video frames."""

    @staticmethod
    def draw_person_box(
        frame: np.ndarray,
        bbox: tuple,
        track_id: Optional[int] = None,
        identity: Optional[str] = None,
        class_name: str = "person",
    ) -> None:
        """
        Draw bounding box and label for a detected person.

        Args:
            frame: Video frame to draw on
            bbox: Bounding box coordinates (x1, y1, x2, y2)
            track_id: Track ID of the person
            identity: Identity name of the person
            class_name: Detected class name
        """
        x1, y1, x2, y2 = bbox

        # Draw bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)

        # Prepare label text
        if identity is not None and track_id is not None:
            label = f"{identity} (ID:{track_id}), {class_name}"
            color = (0, 255, 0)  # Green for identified
        elif track_id is not None:
            if identity == "no id":
                label = f"no id (ID:{track_id})"
                color = (0, 0, 255)  # Red for no identification
            else:
                label = f"Unknown (ID:{track_id})"
                color = (255, 255, 0)  # Yellow for processing
        else:
            label = class_name
            color = (255, 255, 255)  # White for no tracking

        # Draw label
        cv2.putText(
            frame,
            label,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            2,
        )
