from modules.face_monitor import FaceMonitor
import cv2

monitor = FaceMonitor()

while True:

    success, frame = monitor.read_frame()

    if not success:
        break

    faces = monitor.detect_faces(frame)

    for (x, y, w, h) in faces:

        cv2.rectangle(
            frame,
            (x, y),
            (x + w, y + h),
            (0,255,0),
            2
        )

    cv2.imshow("Face Monitor", frame)

    if cv2.waitKey(1) == 27:
        break

monitor.release()

cv2.destroyAllWindows()