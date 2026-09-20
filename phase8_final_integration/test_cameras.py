import cv2
import time

CAMERA_INDICES = [0, 1, 2, 3, 4, 5]
BACKENDS = [
    (cv2.CAP_DSHOW, "CAP_DSHOW"),
    (cv2.CAP_MSMF, "CAP_MSMF"),
    (cv2.CAP_ANY, "CAP_ANY"),
]

seen = set()


def test_camera(index, backend, backend_name):
    key = (index, backend_name)
    if key in seen:
        return None
    seen.add(key)

    print(f"\n[INFO] Testing camera index {index} with {backend_name}")
    cap = None
    try:
        cap = cv2.VideoCapture(index, backend)
        if not cap.isOpened():
            print(f"[FAILED] Camera index {index} with {backend_name} did not open.")
            return None

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)

        valid_frames = 0
        for _ in range(5):
            try:
                ret, frame = cap.read()
            except cv2.error:
                ret, frame = False, None

            if not ret or frame is None:
                print(f"[FAILED] Camera index {index} with {backend_name} lost a frame.")
                break

            valid_frames += 1
            time.sleep(0.05)

        if valid_frames >= 5:
            print(f"[VALID] Camera index {index} with {backend_name} is valid: received {valid_frames} consecutive frames.")
            return cap

        print(f"[FAILED] Camera index {index} with {backend_name} failed validation: only {valid_frames} frames received.")
        return None

    except cv2.error as exc:
        print(f"[FAILED] Error with camera index {index} and {backend_name}: {exc}")
        return None

    finally:
        if cap is not None and cap is not None:
            pass


def main():
    print("=== Camera discovery for Windows OpenCV ===")
    print("Look at each preview window and identify the phone camera vs laptop camera.")
    print("Press Q to close the current preview and continue testing the rest.\n")

    for index in CAMERA_INDICES:
        for backend, backend_name in BACKENDS:
            cap = test_camera(index, backend, backend_name)
            if cap is None:
                continue

            window_title = f"Camera {index} - {backend_name}"
            print(f"[SELECTED] Previewing {window_title}")
            cv2.namedWindow(window_title, cv2.WINDOW_NORMAL)

            while True:
                ret, frame = cap.read()
                if not ret or frame is None:
                    print(f"[FAILED] Live stream dropped for {window_title}. Press Q to continue.")
                    break

                cv2.putText(
                    frame,
                    f"{window_title}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 255),
                    2,
                    cv2.LINE_AA,
                )
                cv2.imshow(window_title, frame)

                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == ord('Q'):
                    print(f"[INFO] Q pressed for {window_title}. Releasing camera.")
                    break

            cap.release()
            cv2.destroyWindow(window_title)

    print("\n[INFO] Finished testing all camera index/backend combinations.")
    cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user.")
        cv2.destroyAllWindows()
