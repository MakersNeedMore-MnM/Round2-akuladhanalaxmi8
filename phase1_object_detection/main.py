"""
AI-Based Smart Drainage Waste Detection and Automatic Segregation System
--------------------------------------------------------------------------
PHASE 1: Real-time Object Detection using Webcam + YOLO

This script:
1. Opens your webcam (built-in or external USB webcam).
2. Loads a pretrained Ultralytics YOLO model (yolo11n.pt).
3. Runs real-time object detection on the video feed.
4. Draws bounding boxes around detected objects.
5. Displays the object's class name and confidence percentage.
6. Displays live FPS (Frames Per Second) on screen.
7. Lets you quit cleanly by pressing the 'Q' key.

NOTE (IMPORTANT):
This is ONLY Phase 1 of the SIH project. The pretrained YOLO model used here
is a GENERAL PURPOSE object detector (trained on the COCO dataset). It does
NOT know about "Plastic", "Organic", or "Metal" waste categories. It will
only detect common everyday objects it was trained on, such as:
    bottle, cup, cell phone, etc.

Future phases will add:
    - A custom-trained waste classification model
      (Plastic / Organic / Metal)
    - Hardware integration (ESP32, servo motors, conveyor/robotic arm)
    - Automatic physical segregation of waste

For now, the goal is simply: CAMERA -> YOLO -> OBJECT DETECTION
"""

import sys
import time

import cv2
from ultralytics import YOLO


# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

# Which YOLO model to use.
# "yolo11n.pt" is the smallest/fastest Ultralytics YOLO11 model.
# It will be AUTOMATICALLY downloaded by the ultralytics library the first
# time this script is run (as long as you have an internet connection).
# After that, it will be cached locally and reused.
MODEL_NAME = "yolo11n.pt"

# Camera index to try first.
#   0 -> usually the built-in / default laptop webcam
#   1 -> usually the first external USB webcam (if 0 is taken by built-in cam)
# If your external webcam doesn't show up, change this to 1 (see README.md).
CAMERA_INDEX = 0

# Minimum confidence required to display a detection (0.0 to 1.0).
# Lower this if the model is missing objects, raise it to reduce false positives.
CONFIDENCE_THRESHOLD = 0.5

# Window title, as required by the project spec.
WINDOW_TITLE = "AI Smart Drainage - Waste Detection"

# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def open_camera(preferred_index: int = 0) -> cv2.VideoCapture:
    """
    Try to open the webcam at `preferred_index`.
    On Windows, cv2.CAP_DSHOW generally gives faster/more reliable camera
    startup than the default backend, so we try that first.

    Returns an opened cv2.VideoCapture object, or exits the program with
    a clear error message if no camera could be opened.
    """
    print(f"[INFO] Attempting to open camera at index {preferred_index} ...")

    # Try DirectShow backend first (best for Windows), then fall back to default.
    backends_to_try = [cv2.CAP_DSHOW, cv2.CAP_ANY]

    for backend in backends_to_try:
        cap = cv2.VideoCapture(preferred_index, backend)
        if cap.isOpened():
            print(f"[INFO] Camera opened successfully "
                  f"(index={preferred_index}, backend={backend}).")
            return cap
        cap.release()

    # If we reach here, the camera could not be opened.
    print("=" * 70)
    print("[ERROR] Could not open the webcam.")
    print(f"        Tried camera index: {preferred_index}")
    print()
    print("Possible reasons and fixes:")
    print("  1. Your webcam is being used by another application")
    print("     (close Zoom/Teams/Camera app and try again).")
    print("  2. Wrong camera index. If you have an external USB webcam,")
    print("     try changing CAMERA_INDEX to 1 (or 2) near the top of")
    print("     main.py, and run the program again.")
    print("  3. Camera drivers are not installed or the camera is not")
    print("     connected properly.")
    print("  4. Windows camera privacy settings are blocking access:")
    print("     Settings -> Privacy & security -> Camera -> allow apps")
    print("     to access your camera.")
    print("=" * 70)
    sys.exit(1)


def load_model(model_name: str) -> YOLO:
    """
    Load a pretrained Ultralytics YOLO model.
    If the model weights are not already downloaded locally, Ultralytics
    will automatically download them the first time this runs.
    """
    print(f"[INFO] Loading YOLO model '{model_name}' ...")
    print("[INFO] (If this is the first run, the model will be "
          "downloaded automatically. This may take a minute.)")
    try:
        model = YOLO(model_name)
    except Exception as exc:  # noqa: BLE001 - we want to show any load error clearly
        print("=" * 70)
        print("[ERROR] Failed to load the YOLO model.")
        print(f"        Reason: {exc}")
        print()
        print("Possible fixes:")
        print("  1. Check your internet connection (needed to download the")
        print("     model the first time).")
        print("  2. Make sure 'ultralytics' is installed correctly:")
        print("     pip install -r requirements.txt")
        print("=" * 70)
        sys.exit(1)

    print("[INFO] Model loaded successfully.")
    return model


def main() -> None:
    print("=" * 70)
    print(" AI-Based Smart Drainage Waste Detection - PHASE 1")
    print(" CAMERA -> YOLO -> OBJECT DETECTION")
    print("=" * 70)

    # 1. Load the YOLO model.
    model = load_model(MODEL_NAME)

    # 2. Open the webcam.
    cap = open_camera(CAMERA_INDEX)

    # Try to set a reasonable resolution. Some webcams ignore this,
    # which is fine - the code will still work with whatever size is returned.
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print("[INFO] Starting real-time detection. Press 'Q' in the video "
          "window to quit.")

    # Variables used to calculate FPS (frames per second).
    prev_frame_time = 0.0

    try:
        while True:
            ret, frame = cap.read()

            if not ret or frame is None:
                print("[WARNING] Failed to read a frame from the camera. "
                      "Stopping.")
                break

            # ---------------------------------------------------------
            # Run YOLO detection on the current frame.
            # verbose=False keeps the console clean (no per-frame logs).
            # conf=CONFIDENCE_THRESHOLD filters out low-confidence detections.
            # ---------------------------------------------------------
            results = model.predict(
                source=frame,
                conf=CONFIDENCE_THRESHOLD,
                verbose=False,
            )

            # results is a list (one entry per input image); we only passed one frame.
            result = results[0]

            # ---------------------------------------------------------
            # Draw bounding boxes + labels manually so we have full control
            # over what's displayed (class name + confidence %).
            # ---------------------------------------------------------
            annotated_frame = frame.copy()

            if result.boxes is not None:
                for box in result.boxes:
                    # Bounding box coordinates (x1, y1, x2, y2) in pixels.
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

                    # Class index and human-readable class name.
                    class_id = int(box.cls[0])
                    class_name = model.names.get(class_id, str(class_id))

                    # Confidence score (0.0 - 1.0) -> convert to percentage.
                    confidence = float(box.conf[0])
                    confidence_pct = confidence * 100

                    # Draw the bounding box rectangle.
                    cv2.rectangle(
                        annotated_frame,
                        (x1, y1),
                        (x2, y2),
                        (0, 255, 0),  # green box (B, G, R)
                        2,
                    )

                    # Prepare the label text: "bottle 87.3%"
                    label = f"{class_name} {confidence_pct:.1f}%"

                    # Draw a filled rectangle behind the text for readability.
                    (text_w, text_h), baseline = cv2.getTextSize(
                        label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
                    )
                    label_y_top = max(y1 - text_h - baseline - 4, 0)
                    cv2.rectangle(
                        annotated_frame,
                        (x1, label_y_top),
                        (x1 + text_w + 4, label_y_top + text_h + baseline + 4),
                        (0, 255, 0),
                        cv2.FILLED,
                    )

                    # Draw the label text on top of that rectangle.
                    cv2.putText(
                        annotated_frame,
                        label,
                        (x1 + 2, label_y_top + text_h + 2),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 0, 0),  # black text
                        2,
                        cv2.LINE_AA,
                    )

            # ---------------------------------------------------------
            # Calculate and display FPS.
            # ---------------------------------------------------------
            current_frame_time = time.time()
            time_diff = current_frame_time - prev_frame_time
            fps = 1.0 / time_diff if time_diff > 0 else 0.0
            prev_frame_time = current_frame_time

            cv2.putText(
                annotated_frame,
                f"FPS: {fps:.1f}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),  # red text
                2,
                cv2.LINE_AA,
            )

            # Small reminder text at the bottom of the frame.
            cv2.putText(
                annotated_frame,
                "Press 'Q' to quit",
                (10, annotated_frame.shape[0] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

            # ---------------------------------------------------------
            # Show the annotated frame in a window with the required title.
            # ---------------------------------------------------------
            cv2.imshow(WINDOW_TITLE, annotated_frame)

            # Wait 1ms for a key press. Quit cleanly if 'Q' or 'q' is pressed.
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == ord("Q"):
                print("[INFO] 'Q' pressed. Shutting down ...")
                break

            # Also allow closing via the window's [X] button.
            if cv2.getWindowProperty(WINDOW_TITLE, cv2.WND_PROP_VISIBLE) < 1:
                print("[INFO] Window closed by user. Shutting down ...")
                break

    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user (Ctrl+C). Shutting down ...")

    finally:
        # ---------------------------------------------------------------
        # ALWAYS release the camera and close windows, even if an error
        # occurred above. This prevents the webcam from staying "locked"
        # after the program exits.
        # ---------------------------------------------------------------
        cap.release()
        cv2.destroyAllWindows()
        print("[INFO] Camera released and windows closed. Goodbye!")


if __name__ == "__main__":
    main()
