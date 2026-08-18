import os
import cv2
import base64
import numpy as np
from insightface.app import FaceAnalysis

# Initialize InsightFace model only once
app = FaceAnalysis(name="buffalo_l")
app.prepare(ctx_id=0 if cv2.cuda.getCudaEnabledDeviceCount() > 0 else -1)

# Similarity threshold
SIMILARITY_THRESHOLD = 0.60


class FaceVerifier:

    def __init__(self):
        self.app = app

    def _load_image(self, image_path):
        return cv2.imread(image_path)

    def _decode_base64(self, image_data):
        if "," in image_data:
            image_data = image_data.split(",")[1]

        image_bytes = base64.b64decode(image_data)
        image = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)

        return image

    def _get_embedding(self, image):

        faces = self.app.get(image)

        if len(faces) == 0:
            return None, "No face detected"

        if len(faces) > 1:
            return None, "Multiple faces detected"

        return faces[0].embedding, None

    def verify(self, registered_photo_path, live_image_base64):

        if not os.path.exists(registered_photo_path):
            return {
                "verified": False,
                "message": "Registration photo not found."
            }

        registered_image = self._load_image(registered_photo_path)
        live_image = self._decode_base64(live_image_base64)

        reg_embedding, error = self._get_embedding(registered_image)

        if error:
            return {
                "verified": False,
                "message": f"Registration Image: {error}"
            }

        live_embedding, error = self._get_embedding(live_image)

        if error:
            return {
                "verified": False,
                "message": f"Live Image: {error}"
            }

        similarity = np.dot(reg_embedding, live_embedding) / (
            np.linalg.norm(reg_embedding) *
            np.linalg.norm(live_embedding)
        )

        verified = similarity >= SIMILARITY_THRESHOLD

        return {
            "verified": verified,
            "similarity": round(float(similarity), 4),
            "threshold": SIMILARITY_THRESHOLD,
            "message": (
                "Identity Verified"
                if verified
                else "Identity Verification Failed"
            )
        }