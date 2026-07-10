"""
Photo capture & validation module.
Owner: Rishabh

The browser (webcam.js) captures the image and sends it to the backend as a
base64-encoded PNG. This module decodes it, uses OpenCV to verify a face is
actually present (basic sanity check against blank/invalid captures), and
saves it to disk. The saved file path is what gets stored in the
candidates.photo_path column in SQLite.
"""

import os
import base64
import uuid
import cv2
import numpy as np

PHOTO_DIR = os.path.join("static", "uploads", "photos")
os.makedirs(PHOTO_DIR, exist_ok=True)

# OpenCV's built-in Haar Cascade for frontal face detection
_face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


def decode_base64_image(data_url: str) -> np.ndarray:
    """
    Converts a base64 data URL (e.g. 'data:image/png;base64,....')
    into an OpenCV-readable image (numpy array, BGR).
    """
    header, encoded = data_url.split(",", 1)
    img_bytes = base64.b64decode(encoded)
    np_arr = np.frombuffer(img_bytes, dtype=np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return image


def contains_face(image: np.ndarray) -> bool:
    """
    Runs face detection on the captured image.
    Returns True if at least one face is detected, False otherwise.
    This is a basic sanity check to reject blank/blocked-camera captures
    at registration time.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = _face_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
    )
    return len(faces) > 0


def save_candidate_photo(data_url: str, candidate_email: str) -> str:
    """
    Decodes, validates, and saves the candidate's registration photo.

    Returns:
        The relative file path to store in the database.

    Raises:
        ValueError: if no face is detected in the captured image.
    """
    image = decode_base64_image(data_url)

    if image is None:
        raise ValueError("Could not decode captured image.")

    if not contains_face(image):
        raise ValueError(
            "No face detected in the captured photo. Please retake it with "
            "your face clearly visible and try again."
        )

    # Unique filename to avoid collisions between candidates
    safe_email = candidate_email.replace("@", "_at_").replace(".", "_")
    filename = f"{safe_email}_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join(PHOTO_DIR, filename)

    cv2.imwrite(filepath, image)

    return filepath
