"""
AI-Based Smart Drainage Waste Detection and Automatic Segregation System
--------------------------------------------------------------------------
PHASE 4: Real-Time Webcam Detection using the Custom Trained YOLO Model

This script:
1. Loads YOUR custom-trained YOLO model (best.pt) from Phase 3.
2. Opens your webcam (built-in or external USB webcam).
3. Runs real-time detection continuously on the video feed.
4. Detects ONLY the 3 waste classes the model was trained on:
       0 = Plastic
       1 = Organic
       2 = Metal
5. Draws bounding boxes around each detected item.
6. Displays the class name, confidence percentage, and live FPS.
7. Lets you quit cleanly by pressing the 'Q' key.

NOTE (IMPORTANT):
This is ONLY Phase 4 of the project. It does NOT:
    - Count detected items (that comes later).
    - Talk to any ESP32 / microcontroller.
    - Control any servo motor or physical hardware.
It ONLY does: CAMERA -> CUSTOM YOLO MODEL -> LIVE DETECTION ON SCREEN.

This script does NOT modify anything inside phase1_object_detection,
phase2_dataset_prep, or phase3_model_training. It only READS the best.pt
file that Phase 3 produced.
"""

import glob
import os
import sys
import time

import cv2


# ---------------------------------------------------------------------------
# CONFIGURATION  (change these values if you need to)
# ---------------------------------------------------------------------------

# Path to your custom-trained model file (best.pt from Phase 3).
#
# Leave this as None to let the script AUTOMATICALLY search for best.pt
# inside "phase3_model_training/runs/.../weights/best.pt".
#
# If auto-detection ever picks the wrong file (e.g. you have several
# training runs), just type the exact path here instead, for example:
#   MODEL_PATH = r"..\phase3_model_training\runs\waste_detector\weights\best.pt"
MODEL_PATH = None

# Camera configuration. Run test_cameras.py first, identify the phone
# camera's index/backend from the preview, then set these values.
# The Droid camera on this setup is index 1 and works with CAP_MSMF.
CAMERA_INDEX = 1
CAMERA_BACKEND = cv2.CAP_MSMF
CAMERA_BACKEND_NAME = "CAP_MSMF"

# Minimum confidence required to display a detection (0.0 to 1.0).
# Lower this if the model is missing objects, raise it to reduce false positives.
CONFIDENCE_THRESHOLD = 0.5

# Window title, as required by the project spec.
WINDOW_TITLE = "AI Smart Drainage - Waste Detection"

# The exact 3 waste classes this model was trained on (Phase 3).
# class_id -> class_name
EXPECTED_CLASSES = {
    0: "Plastic",
    1: "Organic",
    2: "Metal",
}

CATEGORY_COMMANDS = {
    "Plastic": "P",
    "Organic": "O",
    "Metal": "M",
}

# One distinct box color (B, G, R) per class, so it's easy to tell them
# apart on screen at a glance.
CLASS_COLORS = {
    0: (255, 140, 0),    # Plastic  -> orange
    1: (0, 200, 0),      # Organic  -> green
    2: (0, 165, 255),    # Metal    -> amber/gold
}
DEFAULT_BOX_COLOR = (0, 255, 0)  # fallback color, just in case


# ---------------------------------------------------------------------------
# STEP 0: Check that required packages are installed BEFORE doing anything
# else. This gives a clear, friendly message instead of a confusing
# traceback if the user forgot to run "pip install -r requirements.txt".
# ---------------------------------------------------------------------------

def check_dependencies():
    """
    Try importing the packages this script needs.
    If any of them are missing, print a clear message and exit.
    Returns the imported modules (cv2, YOLO) so main() can use them.
    """
    missing = []

    try:
        import cv2  # noqa: F401
    except ImportError:
        missing.append("opencv-python")

    try:
        from ultralytics import YOLO  # noqa: F401
    except ImportError:
        missing.append("ultralytics")

    if missing:
        print("=" * 70)
        print("[ERROR] Missing required package(s):", ", ".join(missing))
        print()
        print("Please install the required packages first by running:")
        print("    pip install -r requirements.txt")
        print()
        print("(or) double-click 'run_detect.bat' which installs everything")
        print("for you automatically.")
        print("=" * 70)
        sys.exit(1)

    # Imports succeeded - import them "for real" now and return them.
    import cv2
    from ultralytics import YOLO
    return cv2, YOLO


# ---------------------------------------------------------------------------
# STEP 1: Locate best.pt
# ---------------------------------------------------------------------------

def find_best_pt():
    """
    Search for best.pt inside the Phase 3 training output folder:
        ../phase3_model_training/runs/.../weights/best.pt

    There can be multiple training runs (train, train2, train3, ...), so
    if more than one best.pt is found, the MOST RECENTLY MODIFIED one is
    used (i.e. your latest/best training attempt).

    Returns the path to best.pt as a string, or None if nothing was found.
    """
    # This file lives in: AI_Smart_Drainage/phase4_webcam_detection/main.py
    # Phase 3 output lives in: AI_Smart_Drainage/phase3_model_training/runs/...
    this_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(this_dir)  # -> AI_Smart_Drainage/

    search_pattern = os.path.join(
        project_root, "phase3_model_training", "runs", "**", "weights", "best.pt"
    )

    candidates = glob.glob(search_pattern, recursive=True)

    if not candidates:
        return None

    # Pick the most recently modified best.pt (the newest training run).
    candidates.sort(key=os.path.getmtime, reverse=True)
    return candidates[0]


def resolve_model_path():
    """
    Decide which best.pt file to load:
      1. If MODEL_PATH was set manually at the top of this file, use it.
      2. Otherwise, try to auto-locate best.pt from Phase 3's output folder.
      3. If neither works, print a clear error message and exit.
    """
    if MODEL_PATH:
        model_path = MODEL_PATH
        print(f"[INFO] Using manually configured MODEL_PATH: {model_path}")

        if not os.path.isfile(model_path):
            print("=" * 70)
            print("[ERROR] The MODEL_PATH set at the top of main.py does not exist:")
            print(f"        {model_path}")
            print()
            print("Fix this by either:")
            print("  1. Correcting the MODEL_PATH value in main.py, or")
            print("  2. Setting MODEL_PATH = None to let the script auto-locate")
            print("     best.pt from phase3_model_training/runs/ automatically.")
            print("=" * 70)
            sys.exit(1)

        return model_path

    # MODEL_PATH is None -> auto-locate it.
    print("[INFO] MODEL_PATH not set - searching for best.pt automatically ...")
    auto_path = find_best_pt()

    if auto_path is None:
        print("=" * 70)
        print("[ERROR] Could not find best.pt anywhere inside:")
        print("        phase3_model_training/runs/.../weights/best.pt")
        print()
        print("Possible fixes:")
        print("  1. Make sure you have completed Phase 3 training and that")
        print("     'best.pt' was saved under phase3_model_training/runs/.")
        print("  2. If best.pt is stored somewhere else, open main.py and set")
        print("     MODEL_PATH near the top of the file to its exact location,")
        print("     for example:")
        print(r'       MODEL_PATH = r"..\phase3_model_training\runs\train\weights\best.pt"')
        print("=" * 70)
        sys.exit(1)

    print(f"[INFO] Found best.pt automatically at: {auto_path}")
    return auto_path


# ---------------------------------------------------------------------------
# STEP 2: Load the custom trained model
# ---------------------------------------------------------------------------

def load_model(YOLO, model_path):
    """
    Load the custom-trained YOLO model (best.pt) from the given path.
    Also checks that the model's classes match what Phase 3 trained
    (Plastic / Organic / Metal), and warns (without crashing) if not.
    """
    print(f"[INFO] Loading custom trained model: {model_path}")
    try:
        model = YOLO(model_path)
    except Exception as exc:  # noqa: BLE001 - show any load error clearly
        print("=" * 70)
        print("[ERROR] Failed to load the model file.")
        print(f"        Path:   {model_path}")
        print(f"        Reason: {exc}")
        print()
        print("Possible fixes:")
        print("  1. Make sure the file is a valid Ultralytics YOLO .pt file")
        print("     produced by Phase 3 training (not corrupted / incomplete).")
        print("  2. Re-check the MODEL_PATH value at the top of main.py.")
        print("  3. Make sure 'ultralytics' and 'torch' are installed correctly:")
        print("     pip install -r requirements.txt")
        print("=" * 70)
        sys.exit(1)

    print("[INFO] Model loaded successfully.")

    # Sanity-check: warn (don't crash) if the model's classes don't match
    # what we expect (Plastic / Organic / Metal). The model might still be
    # usable, e.g. if class order is slightly different, but the user
    # should know.
    model_names = model.names  # dict like {0: 'Plastic', 1: 'Organic', 2: 'Metal'}
    if model_names != EXPECTED_CLASSES:
        print("-" * 70)
        print("[WARNING] The loaded model's classes do not exactly match the")
        print("          expected Phase 3 classes.")
        print(f"          Expected: {EXPECTED_CLASSES}")
        print(f"          Found:    {model_names}")
        print("          Detection will continue, but double-check you loaded")
        print("          the correct best.pt file.")
        print("-" * 70)

    return model


# ---------------------------------------------------------------------------
# STEP 3: Open the webcam
# ---------------------------------------------------------------------------

def prepare_camera_frame(cv2, frame):
    """Return a valid BGR uint8 frame, or None for an unusable frame."""
    try:
        if frame is None or frame.size == 0 or len(frame.shape) not in (2, 3):
            return None
        if len(frame.shape) == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        elif frame.shape[2] == 4:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        elif frame.shape[2] != 3:
            return None
        if str(frame.dtype) != "uint8":
            frame = cv2.normalize(frame, None, 0, 255, cv2.NORM_MINMAX)
            frame = frame.astype("uint8")

        channel_means = cv2.mean(frame)[:3]
        channel_stds = cv2.meanStdDev(frame)[1].flatten()
        green_screen = (
            channel_means[1] > channel_means[0] * 1.5
            and channel_means[1] > channel_means[2] * 1.5
            and max(channel_stds) < 10
        )
        return None if green_screen else frame
    except cv2.error:
        return None


def open_camera(cv2, camera_index: int, backend, backend_name: str):
    """
    Open exactly the camera index/backend selected via test_cameras.py.

    Do not silently fall back to another camera if the selected source fails.
    """
    print(f"[INFO] Opening camera index {camera_index} with {backend_name}")
    cap = None
    try:
        cap = cv2.VideoCapture(camera_index, backend)
        if not cap.isOpened():
            print("=" * 70)
            print(f"[ERROR] Could not open camera index {camera_index} with {backend_name}.")
            print("        Refusing to silently fall back to another camera.")
            print("        Re-run test_cameras.py to confirm the correct index/backend.")
            print("=" * 70)
            sys.exit(1)

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)

        valid_frames = 0
        for _ in range(20):
            try:
                ret, frame = cap.read()
            except cv2.error:
                ret, frame = False, None
            if not ret or frame is None:
                break
            if prepare_camera_frame(cv2, frame) is None:
                break
            valid_frames += 1
            time.sleep(0.05)

        if valid_frames < 20:
            print("=" * 70)
            print(f"[ERROR] Camera index {camera_index} with {backend_name} failed validation "
                  f"({valid_frames}/20 valid frames).")
            print("        Refusing to silently fall back to another camera.")
            print("=" * 70)
            cap.release()
            sys.exit(1)

        print("[INFO] Camera validated with 20 consecutive frames")
        return cap

    except cv2.error as exc:
        if cap is not None:
            cap.release()
        print(f"[ERROR] OpenCV error while opening camera index {camera_index} "
              f"with {backend_name}: {exc}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# MAIN PROGRAM
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 70)
    print(" AI-Based Smart Drainage Waste Detection - PHASE 4")
    print(" CAMERA -> CUSTOM YOLO MODEL -> LIVE WASTE DETECTION")
    print("=" * 70)

    # 0. Make sure required packages are installed.
    cv2, YOLO = check_dependencies()

    # 1. Find and load the custom trained model (best.pt).
    model_path = resolve_model_path()
    model = load_model(YOLO, model_path)

    # 2. This script runs on CPU by default (no GPU required). Ultralytics
    #    will automatically use a GPU if one is available and CUDA is set
    #    up, but everything below works fine on CPU-only machines too.
    device = "cpu"

    # 3. Open the webcam.
    cap = open_camera(cv2, CAMERA_INDEX, CAMERA_BACKEND, CAMERA_BACKEND_NAME)

    # Discard a short warm-up sequence on the same validated capture object.
    for _ in range(15):
        try:
            cap.read()
        except cv2.error as exc:
            print(f"[WARNING] Camera warm-up read failed: {exc}")
        time.sleep(0.05)

    print("[INFO] Starting real-time waste detection (running on CPU).")
    print("[INFO] Press 'Q' in the video window to quit.")

    # Variable used to calculate FPS (frames per second).
    prev_frame_time = 0.0
    frame_format_logged = False
    last_valid_command = None

    # How many consecutive frame-read failures we tolerate before giving up.
    # A single dropped frame shouldn't crash the whole program.
    consecutive_read_failures = 0
    MAX_CONSECUTIVE_READ_FAILURES = 30

    try:
        while True:
            try:
                ret, frame = cap.read()
            except cv2.error as exc:
                ret, frame = False, None
                print(f"[WARNING] Camera frame read failed: {exc}")

            frame = prepare_camera_frame(cv2, frame) if ret else None
            if frame is None:
                consecutive_read_failures += 1
                print(f"[WARNING] Failed to read a frame from the camera "
                      f"({consecutive_read_failures}/{MAX_CONSECUTIVE_READ_FAILURES}).")
                if consecutive_read_failures >= MAX_CONSECUTIVE_READ_FAILURES:
                    print("[ERROR] Too many failed frame reads in a row. "
                          "The camera may have been disconnected. Stopping.")
                    break
                # Skip this loop iteration and try reading the next frame.
                continue

                if not frame_format_logged:
                    print(f"[INFO] Camera frame format: shape={frame.shape}, "
                        f"dtype={frame.dtype}")
                    frame_format_logged = True

            # Reset the failure counter once we successfully read a frame.
            consecutive_read_failures = 0

            # ---------------------------------------------------------
            # Run the custom YOLO model on the current frame.
            # verbose=False keeps the console clean (no per-frame logs).
            # conf=CONFIDENCE_THRESHOLD filters out low-confidence detections.
            # classes=list(EXPECTED_CLASSES) makes sure ONLY Plastic/Organic/
            # Metal are ever detected, even if the model file somehow has
            # extra classes in it.
            # device="cpu" forces CPU-only inference (no GPU required).
            # ---------------------------------------------------------
            results = model.predict(
                source=frame,
                conf=CONFIDENCE_THRESHOLD,
                classes=list(EXPECTED_CLASSES.keys()),
                device=device,
                verbose=False,
            )

            # results is a list (one entry per input image); we only passed one frame.
            result = results[0]

            # ---------------------------------------------------------
            # Draw a separate bounding box + label for every YOLO result in
            # the current frame, and count all detections per class without
            # overwriting earlier results.
            # ---------------------------------------------------------
            annotated_frame = frame.copy()
            detection_counts = {name: 0 for name in EXPECTED_CLASSES.values()}
            detected_category = None
            detected_command = None
            highest_confidence = -1.0

            if result.boxes is not None:
                for box in result.boxes:
                    # Bounding box coordinates (x1, y1, x2, y2) in pixels.
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

                    # Class index and human-readable class name.
                    class_id = int(box.cls[0])
                    class_name = EXPECTED_CLASSES.get(class_id, f"Class {class_id}")
                    if class_name in detection_counts:
                        detection_counts[class_name] += 1

                    # Confidence score (0.0 - 1.0) -> convert to percentage.
                    confidence = float(box.conf[0])
                    confidence_pct = confidence * 100

                    command = CATEGORY_COMMANDS.get(class_name)
                    if command is not None and confidence > highest_confidence:
                        detected_category = class_name
                        detected_command = command
                        highest_confidence = confidence

                    box_color = CLASS_COLORS.get(class_id, DEFAULT_BOX_COLOR)

                    # Draw the bounding box rectangle.
                    cv2.rectangle(
                        annotated_frame,
                        (x1, y1),
                        (x2, y2),
                        box_color,
                        2,
                    )

                    # Prepare the label text: "Plastic 92.4%"
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
                        box_color,
                        cv2.FILLED,
                    )

                    # Draw the label text on top of that rectangle.
                    cv2.putText(
                        annotated_frame,
                        label,
                        (x1 + 2, label_y_top + text_h + 2),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 0, 0),
                        2,
                        cv2.LINE_AA,
                    )

            # ---------------------------------------------------------
            # Display the category-to-command result.
            # ---------------------------------------------------------
            detected_text = detected_category or "None"
            command_text = detected_command or "None"

            if detected_command is not None and detected_command != last_valid_command:
                print(f"{detected_text} detected:")
                print(f"Detected: {detected_text} | Command: {command_text}")
                last_valid_command = detected_command

            cv2.putText(
                annotated_frame,
                f"Detected: {detected_text}",
                (10, 170),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )
            cv2.putText(
                annotated_frame,
                f"Command: {command_text}",
                (10, 200),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2,
                cv2.LINE_AA,
            )

            # ---------------------------------------------------------
            # Calculate and display FPS.
            # ---------------------------------------------------------
            for line_number, class_name in enumerate(EXPECTED_CLASSES.values()):
                cv2.putText(
                    annotated_frame,
                    f"{class_name}: {detection_counts[class_name]}",
                    (10, 65 + line_number * 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),
                    2,
                    cv2.LINE_AA,
                )

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
