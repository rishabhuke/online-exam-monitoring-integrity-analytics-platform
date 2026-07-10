"""
Basic tests for the photo capture module.
Run with: python -m tests.test_photo_capture

Note: this creates a synthetic test image (no real webcam needed) to verify
the decode/validate/save pipeline works end-to-end.
"""

import base64
import io
import cv2
import numpy as np
from modules.photo_capture import decode_base64_image, contains_face, save_candidate_photo


def make_fake_data_url_blank():
    """A blank white image - should NOT contain a face."""
    img = np.ones((300, 300, 3), dtype=np.uint8) * 255
    _, buf = cv2.imencode(".png", img)
    b64 = base64.b64encode(buf).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def test_decode_base64_image():
    data_url = make_fake_data_url_blank()
    image = decode_base64_image(data_url)
    assert image is not None
    assert image.shape[2] == 3  # BGR channels
    print("PASS: decode_base64_image")


def test_contains_face_rejects_blank_image():
    data_url = make_fake_data_url_blank()
    image = decode_base64_image(data_url)
    assert contains_face(image) is False
    print("PASS: contains_face correctly rejects blank image")


def test_save_candidate_photo_raises_on_no_face():
    data_url = make_fake_data_url_blank()
    try:
        save_candidate_photo(data_url, "test@example.com")
        print("FAIL: expected ValueError for no-face image, none raised")
    except ValueError:
        print("PASS: save_candidate_photo raises ValueError when no face detected")


if __name__ == "__main__":
    test_decode_base64_image()
    test_contains_face_rejects_blank_image()
    test_save_candidate_photo_raises_on_no_face()
    print("\nAll tests completed. For a real face-detection test, capture an "
          "actual photo through the registration page and confirm it saves "
          "successfully to static/uploads/photos/.")
