import os
import cv2
import base64
import numpy as np
from datetime import datetime
from insightface.app import FaceAnalysis


# -------------------------------------------------
# Load InsightFace Model (only once)
# -------------------------------------------------

app = FaceAnalysis(name="buffalo_l")

app.prepare(
    ctx_id=0
    if cv2.cuda.getCudaEnabledDeviceCount() > 0
    else -1
)

SIMILARITY_THRESHOLD = 0.60


class FaceMonitor:

    def __init__(self):
        self.app = app

    # -------------------------------------------------
    # Load Registration Image
    # -------------------------------------------------

    def _load_image(self, path):

        if not path:
            return None

        if not os.path.exists(path):
            return None

        return cv2.imread(path)

    # -------------------------------------------------
    # Decode Live Image
    # -------------------------------------------------

    def _decode_base64(self, image_data):

        try:

            if not image_data:
                return None

            if "," in image_data:
                image_data = image_data.split(",", 1)[1]

            image_bytes = base64.b64decode(
                image_data
            )

            image_array = np.frombuffer(
                image_bytes,
                np.uint8
            )

            image = cv2.imdecode(
                image_array,
                cv2.IMREAD_COLOR
            )

            return image

        except Exception:

            return None

    # -------------------------------------------------
    # Cosine Similarity
    # -------------------------------------------------

    def _similarity(self, emb1, emb2):

        denominator = (

            np.linalg.norm(emb1)

            *

            np.linalg.norm(emb2)

        )

        if denominator == 0:

            return 0.0

        return float(

            np.dot(emb1, emb2)

            /

            denominator

        )

    # -------------------------------------------------
    # Save Evidence
    # -------------------------------------------------

    def _save_evidence(

        self,

        image,

        folder

    ):

        os.makedirs(
            folder,
            exist_ok=True
        )

        filename = datetime.now().strftime(

            "%Y%m%d_%H%M%S_%f"

        ) + ".jpg"

        filepath = os.path.join(

            folder,

            filename

        )

        cv2.imwrite(
            filepath,
            image
        )

        return filepath

    # -------------------------------------------------
    # Save Latest Monitoring Frame
    # -------------------------------------------------

    def save_latest_frame(

        self,

        image,

        candidate_id,

        exam_id

    ):

        try:

            folder = os.path.join(

                "evidence",

                f"candidate_{candidate_id}",

                f"exam_{exam_id}",

                "live"

            )

            os.makedirs(

                folder,

                exist_ok=True

            )

            filepath = os.path.join(

                folder,

                "latest.jpg"

            )

            cv2.imwrite(

                filepath,

                image

            )

            return filepath

        except Exception as error:

            print(
                "Save latest frame error:",
                repr(error)
            )

            return None

    # -------------------------------------------------
    # Monitor Candidate
    # -------------------------------------------------

    def monitor(

        self,

        registered_photo,

        live_image_base64,

        candidate_id,

        exam_id

    ):

        try:

            # -----------------------------------------
            # LOAD REGISTERED IMAGE
            # -----------------------------------------

            registered = self._load_image(

                registered_photo

            )

            if registered is None:

                return {

                    "status": "error",

                    "message":
                        "Registration photo missing"

                }

            # -----------------------------------------
            # DECODE LIVE CAMERA IMAGE
            # -----------------------------------------

            live = self._decode_base64(

                live_image_base64

            )

            if live is None:

                return {

                    "status": "error",

                    "message":
                        "Invalid live image"

                }

            # -----------------------------------------
            # SAVE LATEST FRAME
            #
            # This is used by the ADMIN LIVE
            # MONITORING dashboard.
            # -----------------------------------------

            latest_frame = self.save_latest_frame(

                live,

                candidate_id,

                exam_id

            )

            # -----------------------------------------
            # REGISTERED FACE
            # -----------------------------------------

            registered_faces = self.app.get(

                registered

            )

            if len(registered_faces) != 1:

                return {

                    "status": "error",

                    "message":
                        "Invalid registration image",

                    "latest_frame":
                        latest_frame

                }

            # -----------------------------------------
            # LIVE FACE DETECTION
            # -----------------------------------------

            live_faces = self.app.get(

                live

            )

            # -----------------------------------------
            # EVIDENCE ROOT
            # -----------------------------------------

            evidence_root = os.path.join(

                "evidence",

                f"candidate_{candidate_id}",

                f"exam_{exam_id}"

            )

            # -----------------------------------------
            # NO FACE
            # -----------------------------------------

            if len(live_faces) == 0:

                evidence = self._save_evidence(

                    live,

                    os.path.join(

                        evidence_root,

                        "no_face"

                    )

                )

                return {

                    "status":
                        "violation",

                    "type":
                        "NO_FACE",

                    "message":
                        "No face detected.",

                    "evidence":
                        evidence,

                    "latest_frame":
                        latest_frame

                }

            # -----------------------------------------
            # MULTIPLE FACES
            # -----------------------------------------

            if len(live_faces) > 1:

                evidence = self._save_evidence(

                    live,

                    os.path.join(

                        evidence_root,

                        "multiple_faces"

                    )

                )

                return {

                    "status":
                        "violation",

                    "type":
                        "MULTIPLE_FACES",

                    "message":
                        "Multiple faces detected.",

                    "face_count":
                        len(live_faces),

                    "evidence":
                        evidence,

                    "latest_frame":
                        latest_frame

                }

            # -----------------------------------------
            # FACE SIMILARITY
            # -----------------------------------------

            similarity = self._similarity(

                registered_faces[0].embedding,

                live_faces[0].embedding

            )

            # -----------------------------------------
            # WRONG CANDIDATE
            # -----------------------------------------

            if similarity < SIMILARITY_THRESHOLD:

                evidence = self._save_evidence(

                    live,

                    os.path.join(

                        evidence_root,

                        "unknown_face"

                    )

                )

                return {

                    "status":
                        "violation",

                    "type":
                        "UNKNOWN_FACE",

                    "similarity":
                        round(
                            similarity,
                            4
                        ),

                    "message":
                        "Identity mismatch.",

                    "evidence":
                        evidence,

                    "latest_frame":
                        latest_frame

                }

            # -----------------------------------------
            # VERIFIED
            # -----------------------------------------

            return {

                "status":
                    "ok",

                "similarity":
                    round(
                        similarity,
                        4
                    ),

                "message":
                    "Candidate verified",

                "latest_frame":
                    latest_frame

            }

        except Exception as e:

            print(
                "Face monitoring error:",
                repr(e)
            )

            return {

                "status":
                    "error",

                "message":
                    str(e)

            }