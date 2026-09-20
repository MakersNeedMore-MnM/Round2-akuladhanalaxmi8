"""
Camera scanner/preview tool.

Scans camera indices 0-5, tries CAP_DSHOW, CAP_MSMF, and CAP_ANY for each
index, and shows a live preview window for every camera that validates.
"""

import cv2
import time


BACKENDS = [
    (cv2.CAP_DSHOW, "CAP_DSHOW"),
    (cv2.CAP_MSMF, "CAP_MSMF"),
    (cv2.CAP_ANY, "CAP_ANY"),
]

INDEX_RANGE = range(0, 6)


def try_camera(index, backend, backend_name):
    print(f"\n[INFO] Testing camera index {index} with {backend_name}")
    cap = None
    try:
        cap = cv2.VideoCapture(index, backend)
        if not cap.isOpened():
            print(f"[INFO] Camera index {index} with {backend_name} did not open.")
            cap.release()
            return None

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)

        frames_received = 0
        for _ in range(5):
            try:
                ret, frame = cap.read()
            except cv2.error:
                ret, frame = False, None

            if not ret or frame is None:
                print(f"[WARN] Frame read failed for camera index {index} with {backend_name}.")
                break

            frames_received += 1
            time.sleep(0.05)

        if frames_received >= 5:
            print(f"[INFO] Camera index {index} with {backend_name} is valid: "
                  f"received {frames_received} consecutive frames.")
            return cap

        print(f"[INFO] Camera index {index} with {backend_name} failed validation: "
              f"only {frames_received} frames received.")
        cap.release()
        return None

    except cv2.error as exc:
        print(f"[ERROR] Camera index {index} with {backend_name} raised OpenCV error: {exc}")
        if cap is not None:
            cap.release()
        return None


def preview_camera(cap, index, backend_name):
    """Show a live preview. Press Q to close it and continue scanning."""
    window_title = f"Camera {index} - {backend_name}  (press Q to continue scanning)"
    cv2.namedWindow(window_title, cv2.WINDOW_NORMAL)

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            print(f"[WARN] Live stream lost for camera index {index} with {backend_name}; "
                  "press Q to continue testing.")
            break

        cv2.putText(
            frame,
            f"Camera {index} | {backend_name}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.imshow(window_title, frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == ord("Q"):
            break

    cv2.destroyWindow(window_title)


def main():
    found_cameras = []

    for index in INDEX_RANGE:
        for backend, backend_name in BACKENDS:
            cap = try_camera(index, backend, backend_name)
            if cap is None:
                continue

            print(f"[INFO] Valid camera found at index {index}, backend {backend_name}. "
                  "Opening preview -- press Q to continue scanning.")
            preview_camera(cap, index, backend_name)
            cap.release()
            cv2.destroyAllWindows()
            found_cameras.append((index, backend_name))

    print("\n" + "=" * 70)
    print("[INFO] Finished testing camera indices 0 through 5.")
    if found_cameras:
        print("[INFO] Valid camera/backend combinations found:")
        for i, (index, backend_name) in enumerate(found_cameras):
            print(f"    [{i}] index={index}  backend={backend_name}")
        print("\nNote which [i] showed your PHONE (DroidCam) feed, then set")
        print("CAMERA_INDEX / CAMERA_BACKEND in main.py to that index/backend.")
    else:
        print("[WARNING] No valid cameras were found at all.")
    print("=" * 70)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
