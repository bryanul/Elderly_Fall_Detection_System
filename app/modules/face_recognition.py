"""Face recognition utilities for embedding and identification."""

from typing import Dict, List, Optional
import os

import cv2
import numpy as np
from lightphe import LightPHE

from deepface import DeepFace

# --- LightPHE key management ---
KEY_DIR = os.path.dirname(__file__)
SECRET_KEY_PATH = os.path.join(KEY_DIR, "lightphe_secret.txt")   # privada
PUBLIC_KEY_PATH = os.path.join(KEY_DIR, "lightphe_public.txt")   # pública (opcional)

def get_lightphe(precision: int = 19):
    """
    Devuelve una instancia de LightPHE usando Paillier.
    - Si no existen llaves: las genera y las guarda.
    - Si ya existen: las reutiliza sin regenerar.
    """
    # 1) Si ya existe la privada, cargar directamente sin regenerar
    if os.path.exists(SECRET_KEY_PATH):
        return LightPHE(algorithm_name="Paillier", precision=precision, key_file=SECRET_KEY_PATH)

    # 2) No existe: crear instancia nueva (esto genera el par en memoria)
    cs = LightPHE(algorithm_name="Paillier", precision=precision)

    # 3) Guardar llaves en disco (privada + pública)
    #    Nota: exporta la privada por defecto; para la pública usar public=True
    cs.export_keys(SECRET_KEY_PATH)
    cs.export_keys(PUBLIC_KEY_PATH, public=True)

    # 4) (Opcional) Reabrir desde archivo para asegurarnos que se restauran bien
    return LightPHE(algorithm_name="Paillier", precision=precision, key_file=SECRET_KEY_PATH)

# --- Uso en tu programa ---
cs = get_lightphe(precision=19)


def embed_face(img_bytes: bytes):
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
    embedding = DeepFace.represent(
        img,
        model_name="VGG-Face",
        detector_backend="yolov11n",
        enforce_detection=False,
        align=True,
        max_faces=1,
    )[0]["embedding"]
    encrypted_embedding = cs.encrypt(embedding)
    return encrypted_embedding


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

    def identify_face(self, embedding):
        """
        Identify a face based on its embedding.

        Args:
            embedding: Face embedding to identify

        Returns:
            Name of identified person or None if no match found
        """
        min_dist = float("inf")
        identity = None
        best_score = None

        for name, db_emb in self.face_db.items():
            try:
                encrypted_cosine_similarity = db_emb @ embedding
                calculated_similarity = cs.decrypt(encrypted_cosine_similarity)[0]
                print(f"Comparando con: {name}, score: {calculated_similarity}")
                if calculated_similarity >= self.threshold:
                    print(f"¡MATCH! {name} (score: {calculated_similarity})")
                    return name
                # Guardar el mejor score aunque no haya match
                if best_score is None or calculated_similarity > best_score:
                    best_score = calculated_similarity
                    identity = name
            except Exception as e:
                print(f"Error in homomorphic comparison for {name}: {e}")
        print(f"No match. Mejor score: {best_score} con {identity}")
        return None

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
