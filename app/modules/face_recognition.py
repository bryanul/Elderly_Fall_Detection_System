"""Face recognition utilities for embedding and identification."""

from typing import Dict, List, Optional

import cv2
import numpy as np

from deepface import DeepFace


def embed_face(img_bytes: bytes) -> List[float]:
    """
    Extract face embedding from image bytes.

    Args:
        img_bytes: Raw image bytes

    Returns:
        Face embedding as a list of floats

    Raises:
        Exception: If face embedding extraction fails
    """
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return DeepFace.represent(
        img,
        model_name="VGG-Face",
        detector_backend="yolov11n",
        enforce_detection=False,
        align=True,
        max_faces=1,
    )[0]["embedding"]


class FaceIdentifier:
    """Handles face identification against a known face database."""

    def __init__(self, face_db: Dict[str, List[float]], threshold: float = 1.22):
        """
        Initialize face identifier.

        Args:
            face_db: Dictionary mapping names to face embeddings
            threshold: Distance threshold for face identification
        """
        self.face_db = face_db
        self.threshold = threshold

    def identify_face(self, embedding: List[float]) -> Optional[str]:
        """
        Identify a face based on its embedding.

        Args:
            embedding: Face embedding to identify

        Returns:
            Name of identified person or None if no match found
        """
        min_dist = float("inf")
        identity = None

        for name, db_emb in self.face_db.items():
            db_emb_np = np.array(db_emb)
            embedding_np = np.array(embedding)
            dist = np.linalg.norm(db_emb_np - embedding_np)
            if dist < min_dist and dist < self.threshold:
                min_dist = dist
                identity = name
        return identity

    def extract_and_identify_face(self, person_crop: np.ndarray) -> Optional[str]:
        """
        Extract face embedding from person crop and identify.

        Args:
            person_crop: Cropped image of person

        Returns:
            Identity name or None if identification fails
        """
        try:
            embedding = DeepFace.represent(
                person_crop,
                model_name="VGG-Face",
                detector_backend="yolov11n",
                enforce_detection=False,
                align=True,
                max_faces=1,
            )[0]["embedding"]
            return self.identify_face(embedding)
        except Exception as e:
            print(e)
            return None
