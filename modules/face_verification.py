import os
import cv2
import base64
import numpy as np
from insightface.app import FaceAnalysis


# ---------------------------------------------------------
# Initialize InsightFace only once
# ---------------------------------------------------------

app = FaceAnalysis(name="buffalo_l")

app.prepare(
    ctx_id=0 if cv2.cuda.getCudaEnabledDeviceCount() > 0 else -1
)


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

SIMILARITY_THRESHOLD = 0.60


# ---------------------------------------------------------
# Face Verifier
# ---------------------------------------------------------

class FaceVerifier:

    def __init__(self):
        self.app = app

    # -----------------------------------------------------
    # Load Registration Image
    # -----------------------------------------------------

    def _load_image(self, image_path):

        if not os.path.exists(image_path):
            return None

        return cv2.imread(image_path)

    # -----------------------------------------------------
    # Decode Base64 Image
    # -----------------------------------------------------

    def _decode_base64(self, image_data):

        try:

            if "," in image_data:
                image_data = image_data.split(",")[1]

            image_bytes = base64.b64decode(image_data)

            image_array = np.frombuffer(
                image_bytes,
                dtype=np.uint8
            )

            image = cv2.imdecode(
                image_array,
                cv2.IMREAD_COLOR
            )

            return image

        except Exception:

            return None

    # -----------------------------------------------------
    # Extract Face Embedding
    # -----------------------------------------------------

    def _get_embedding(self, image):

        if image is None:

            return None, "Unable to load image."

        try:

            faces = self.app.get(image)

        except Exception as e:

            return None, str(e)

        if len(faces) == 0:

            return None, "No face detected."

        if len(faces) > 1:

            return None, "Multiple faces detected."

        return faces[0].embedding, None

    # -----------------------------------------------------
    # Cosine Similarity
    # -----------------------------------------------------

    def _cosine_similarity(self, emb1, emb2):

        emb1 = np.asarray(emb1)
        emb2 = np.asarray(emb2)

        similarity = np.dot(emb1, emb2) / (

            np.linalg.norm(emb1) *
            np.linalg.norm(emb2)

        )

        return float(similarity)

    # -----------------------------------------------------
    # Verify Candidate
    # -----------------------------------------------------

    def verify(
        self,
        registered_photo_path,
        live_image_base64
    ):

        try:

            # ---------------------------------------------
            # Load Images
            # ---------------------------------------------

            registered_image = self._load_image(
                registered_photo_path
            )

            if registered_image is None:

                return {

                    "verified": False,

                    "similarity": 0,

                    "threshold": SIMILARITY_THRESHOLD,

                    "message":
                        "Registration photo not found."

                }

            live_image = self._decode_base64(
                live_image_base64
            )

            if live_image is None:

                return {

                    "verified": False,

                    "similarity": 0,

                    "threshold": SIMILARITY_THRESHOLD,

                    "message":
                        "Invalid live image."

                }

            # ---------------------------------------------
            # Registration Face
            # ---------------------------------------------

            registered_embedding, error = self._get_embedding(
                registered_image
            )

            if error:

                return {

                    "verified": False,

                    "similarity": 0,

                    "threshold": SIMILARITY_THRESHOLD,

                    "message":
                        f"Registration Image: {error}"

                }

            # ---------------------------------------------
            # Live Face
            # ---------------------------------------------

            live_embedding, error = self._get_embedding(
                live_image
            )

            if error:

                return {

                    "verified": False,

                    "similarity": 0,

                    "threshold": SIMILARITY_THRESHOLD,

                    "message":
                        f"Live Image: {error}"

                }

            # ---------------------------------------------
            # Compare Faces
            # ---------------------------------------------

            similarity = self._cosine_similarity(
                registered_embedding,
                live_embedding
            )

            verified = similarity >= SIMILARITY_THRESHOLD

            return {

                "verified": verified,

                "similarity": round(similarity, 4),

                "threshold": SIMILARITY_THRESHOLD,

                "message":

                    "Identity Verified"

                    if verified

                    else

                    "Identity Verification Failed"

            }

        except Exception as e:

            return {

                "verified": False,

                "similarity": 0,

                "threshold": SIMILARITY_THRESHOLD,

                "message": f"Verification Error: {str(e)}"

            }