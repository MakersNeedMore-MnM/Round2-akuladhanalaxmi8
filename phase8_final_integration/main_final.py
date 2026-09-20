"""
AI-Based Smart Drainage Waste Detection and Automatic Segregation System
--------------------------------------------------------------------------
PHASE 8: Final Integration (PART 1)

This script reuses:
    - The custom-trained YOLO model (best.pt) produced by Phase 3.
    - The persistent-tracking + unique-counting logic proven in Phase 5.

It does NOT reuse Phase 5's file directly - it is a clean, self-contained
"final" entry point for the integrated system, so later parts of Phase 8
(ESP32 communication, servo sorting) can be layered onto this file without
touching Phases 1-7 at all.

This script:
1. Automatically finds best.pt from Phase 3's output folder:
       phase3_model_training/runs/**/weights/best.pt
   (Also supports a manually configured MODEL_PATH override below.)
2. Opens the webcam (CAMERA_INDEX, default 0 - change to 1 for an
   external USB webcam) using OpenCV.
3. Runs YOLO TRACKING (not plain detection), giving each physical
   object a persistent tracking ID.
4. Detects only: Plastic, Organic, Metal.
5. Displays, for every detected object:
       - bounding box
       - class name
       - confidence
       - tracking ID
   ...plus a live FPS counter.
6. Counts each tracking ID only ONCE (see count_utils.py).
7. Displays live counts on-screen:
       Plastic: X
       Organic: X
       Metal:   X
       Total:   X
8. Press 'R' to reset all counts back to zero.
9. Press 'Q' to safely quit (camera + windows are always released).
10. Runs entirely on CPU - no GPU required.

NOTE (PHASE 8 - ESP32 SERIAL COMMUNICATION ADDED):
This part now sends the category of each newly counted object to an
ESP32 over USB serial (see serial_controller.py, reusing the Phase 6
communication conventions). It still does NOT control any servo motor
or physical sorting gate - that remains a later part of Phase 8.
If USE_ESP32 is set to False in serial_controller.py, or no ESP32 is
connected, this program keeps running normally in DEMO MODE.

This script does NOT modify anything inside phase1_object_detection,
phase2_dataset_prep, phase3_model_training, phase4_webcam_detection,
phase5_waste_counting, phase6_esp32_communication, or
phase7_servo_sorting. It only READS the best.pt file that Phase 3
produced (the exact same way Phase 4 and Phase 5 do).
"""

import glob
import os
import sys
import time

from count_utils import TrackCounter
from serial_controller import (
    USE_ESP32,
    connect_esp32,
    send_to_esp32,
    close_connection,
)


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

# Camera index and backend to use for the phone/DroidCam camera.
# These values were confirmed by running test_cameras.py on this machine.
# Keep this as the fixed phone camera source instead of silently switching.
CAMERA_INDEX = 0
CAMERA_BACKEND = None

# Minimum confidence required to display/track a detection (0.0 to 1.0).
# Lower this if the model is missing objects, raise it to reduce false positives.
CONFIDENCE_THRESHOLD = 0.5

# Which YOLO tracker to use. "bytetrack.yaml" ships with ultralytics and
# is lightweight/fast, which is ideal for CPU-only machines.
TRACKER_CONFIG = "bytetrack.yaml"

# Window title.
WINDOW_TITLE = "AI Smart Drainage - Phase 8: Final Integration"

# The exact 3 waste classes this model was trained on (Phase 3).
# class_id -> class_name
EXPECTED_CLASSES = {
    0: "Plastic",
    1: "Organic",
    2: "Metal",
}

# One distinct box color (B, G, R) per class, so it's easy to tell them
# apart on screen at a glance. Same colors as Phase 4/5 for consistency.
CLASS_COLORS = {
    0: (255, 140, 0),    # Plastic  -> orange
    1: (0, 200, 0),      # Organic  -> green
    2: (0, 165, 255),    # Metal    -> amber/gold
}
DEFAULT_BOX_COLOR = (0, 255, 0)  # fallback color, just in case

# Order in which counts are displayed on screen.
COUNT_DISPLAY_ORDER = ["Plastic", "Organic", "Metal"]

# Minimum time (in seconds) to wait between two ESP32 sort commands.
# This gives the physical sorting mechanism time to act before the next
# command is sent, even if several new objects are counted in quick
# succession. Change USE_ESP32 / SERIAL_PORT / BAUD_RATE in
# serial_controller.py, not here.
SORTING_COOLDOWN_SECONDS = 2


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
        print("=" * 70)
        sys.exit(1)

    # Imports succeeded - import them "for real" now and return them.
    import cv2
    from ultralytics import YOLO
    return cv2, YOLO


# ---------------------------------------------------------------------------
# STEP 1: Locate best.pt  (same logic as Phase 4/5, so every phase always
# agrees on which trained model file to use)
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
    # This file lives in: AI_Smart_Drainage/phase8_final_integration/main_final.py
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
            print("[ERROR] The MODEL_PATH set at the top of main_final.py does not exist:")
            print(f"        {model_path}")
            print()
            print("Fix this by either:")
            print("  1. Correcting the MODEL_PATH value in main_final.py, or")
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
        print("  2. If best.pt is stored somewhere else, open main_final.py and")
        print("     set MODEL_PATH near the top of the file to its exact location,")
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
        print("  2. Re-check the MODEL_PATH value at the top of main_final.py.")
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
        print("          Detection/counting will continue, but double-check you")
        print("          loaded the correct best.pt file.")
        print("-" * 70)

    return model


# ---------------------------------------------------------------------------
# STEP 3: Open the webcam
# ---------------------------------------------------------------------------

def open_camera(cv2, index: int, backend: int):
    """
    Open the already-confirmed phone/DroidCam camera at the exact index/backend.
    Do not silently scan/fallback to another camera; if it cannot be opened
    or does not deliver frames, the program exits with a clear message.
    """
    print(f"[INFO] Connecting to phone camera...")
    print(f"[INFO] Camera index: {index}")
    print(f"[INFO] Backend: {backend}")

    cap = cv2.VideoCapture(index, backend)
    if not cap.isOpened():
        print("=" * 70)
        print("[ERROR] Could not open the phone/DroidCam camera at the")
        print(f"        configured index={index}, backend={backend}.")
        print("        The laptop webcam will NOT be used as a silent fallback.")
        print("        Fix: run test_cameras.py again and confirm the active")
        print("        DroidCam index/backend before running the project.")
        print("=" * 70)
        sys.exit(1)

    ret, frame = cap.read()
    if not ret or frame is None:
        print("[ERROR] Camera opened but is not sending frames. Aborting.")
        cap.release()
        sys.exit(1)

    print("[INFO] Phone camera found!")
    print(f"[INFO] Camera index: {index}")
    print(f"[INFO] Backend: {backend}")
    return cap


# ---------------------------------------------------------------------------
# STEP 4: Drawing helpers (keeps the main loop below easy to read)
# ---------------------------------------------------------------------------

def draw_detection_box(cv2, frame, x1, y1, x2, y2, class_name, confidence, track_id, box_color):
    """
    Draw one bounding box + label showing class name, confidence, and
    tracking ID, e.g.:  "Plastic ID:3 92.4%"
    """
    cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)

    confidence_pct = confidence * 100
    track_label = f"ID:{track_id}" if track_id is not None else "ID:--"
    label = f"{class_name} {track_label} {confidence_pct:.1f}%"

    (text_w, text_h), baseline = cv2.getTextSize(
        label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2
    )
    label_y_top = max(y1 - text_h - baseline - 4, 0)
    cv2.rectangle(
        frame,
        (x1, label_y_top),
        (x1 + text_w + 4, label_y_top + text_h + baseline + 4),
        box_color,
        cv2.FILLED,
    )
    cv2.putText(
        frame,
        label,
        (x1 + 2, label_y_top + text_h + 2),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 0, 0),  # black text
        2,
        cv2.LINE_AA,
    )


def draw_count_panel(cv2, frame, counter: TrackCounter):
    """
    Draw a semi-transparent panel in the top-left corner showing the
    live, category-wise unique-object counts, e.g.:

        WASTE COUNT
        Plastic: 4
        Organic: 2
        Metal:   1
        Total:   7
    """
    lines = ["WASTE COUNT"]
    counts = counter.get_counts()
    for class_name in COUNT_DISPLAY_ORDER:
        lines.append(f"{class_name}: {counts.get(class_name, 0)}")
    lines.append(f"Total: {counter.get_total()}")

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.7
    thickness = 2
    line_height = 28
    padding = 12

    panel_width = max(
        cv2.getTextSize(line, font, font_scale, thickness)[0][0] for line in lines
    ) + (padding * 2)
    panel_height = (line_height * len(lines)) + padding

    # Semi-transparent black background for readability over any scene.
    overlay = frame.copy()
    cv2.rectangle(overlay, (10, 10), (10 + panel_width, 10 + panel_height), (0, 0, 0), cv2.FILLED)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

    y = 10 + padding + 18
    for i, line in enumerate(lines):
        color = (0, 255, 255) if i == 0 else (255, 255, 255)
        cv2.putText(frame, line, (10 + padding, y), font, font_scale, color, thickness, cv2.LINE_AA)
        y += line_height


def draw_footer_hints(cv2, frame):
    """Reminder text at the bottom of the frame for the keyboard controls."""
    cv2.putText(
        frame,
        "Press 'R' to reset counts   |   Press 'Q' to quit",
        (10, frame.shape[0] - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )


# ---------------------------------------------------------------------------
# MAIN PROGRAM
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 70)
    print(" AI-Based Smart Drainage Waste Detection - PHASE 8 (Part 1)")
    print(" CAMERA -> CUSTOM YOLO MODEL + TRACKING -> UNIQUE WASTE COUNTING")
    print(" (ESP32 / servo integration will be added in a later part)")
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

    # 3. Set up the counter that tracks which object IDs have already
    #    been counted, per class (see count_utils.py for the full logic).
    counter = TrackCounter(EXPECTED_CLASSES)

    # 3b. Try to connect to the ESP32 (Phase 6 conventions, reused via
    #     serial_controller.py). If USE_ESP32 is False, or the ESP32 is
    #     not reachable, this program keeps running normally in DEMO MODE.
    if USE_ESP32:
        print("[INFO] USE_ESP32 = True - attempting to connect to ESP32 ...")
        connect_esp32()
    else:
        print("[INFO] USE_ESP32 = False - running in DEMO MODE (no ESP32 commands sent).")

    # Timestamp of the last command sent to the ESP32, used together with
    # SORTING_COOLDOWN_SECONDS so newly counted objects don't flood the
    # sorter with commands faster than it can physically act.
    last_sort_send_time = 0.0

    # 4. Open the fixed phone/DroidCam camera using the backend confirmed by test_cameras.py.
    if CAMERA_BACKEND is None:
        CAMERA_BACKEND = cv2.CAP_DSHOW
    cap = open_camera(cv2, CAMERA_INDEX, CAMERA_BACKEND)

    # Try to set a reasonable resolution. Some webcams ignore this,
    # which is fine - the code will still work with whatever size is returned.
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print("[INFO] Starting real-time waste tracking + counting (running on CPU).")
    print("[INFO] Press 'R' to reset counts. Press 'Q' to quit.")

    # Variable used to calculate FPS (frames per second).
    prev_frame_time = 0.0

    # How many consecutive frame-read failures we tolerate before giving up.
    # A single dropped frame shouldn't crash the whole program.
    consecutive_read_failures = 0
    MAX_CONSECUTIVE_READ_FAILURES = 30

    try:
        while True:
            ret, frame = cap.read()

            if not ret or frame is None:
                consecutive_read_failures += 1
                print(f"[WARNING] Failed to read a frame from the camera "
                      f"({consecutive_read_failures}/{MAX_CONSECUTIVE_READ_FAILURES}).")
                if consecutive_read_failures >= MAX_CONSECUTIVE_READ_FAILURES:
                    print("[ERROR] Too many failed frame reads in a row. "
                          "The camera may have been disconnected. Stopping.")
                    break
                # Skip this loop iteration and try reading the next frame.
                continue

            # Reset the failure counter once we successfully read a frame.
            consecutive_read_failures = 0

            # ---------------------------------------------------------
            # Run YOLO TRACKING (not plain .predict()) on the current
            # frame. This is what gives each physical object a
            # persistent tracking ID that stays the same across frames.
            #
            #   persist=True   -> remember tracked objects between calls
            #                      (required for IDs to stay consistent
            #                      frame-to-frame instead of resetting).
            #   tracker=...    -> lightweight ByteTrack config, good for CPU.
            #   conf=...       -> confidence threshold.
            #   classes=...    -> only ever consider Plastic/Organic/Metal.
            #   device="cpu"   -> force CPU-only inference.
            #   verbose=False  -> keep the console clean.
            # ---------------------------------------------------------
            results = model.track(
                source=frame,
                persist=True,
                tracker=TRACKER_CONFIG,
                conf=CONFIDENCE_THRESHOLD,
                classes=list(EXPECTED_CLASSES.keys()),
                device=device,
                verbose=False,
            )

            # results is a list (one entry per input image); we only passed one frame.
            result = results[0]

            annotated_frame = frame.copy()

            if result.boxes is not None:
                for box in result.boxes:
                    # Bounding box coordinates (x1, y1, x2, y2) in pixels.
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

                    # Class index and human-readable class name.
                    class_id = int(box.cls[0])
                    class_name = EXPECTED_CLASSES.get(class_id, f"Class {class_id}")

                    # Confidence score (0.0 - 1.0).
                    confidence = float(box.conf[0])

                    # Persistent tracking ID for this physical object.
                    # box.id is None if the tracker hasn't assigned an ID
                    # yet for this detection (e.g. very first frame or a
                    # momentary tracking gap) - handled safely.
                    track_id = int(box.id[0]) if box.id is not None else None

                    box_color = CLASS_COLORS.get(class_id, DEFAULT_BOX_COLOR)

                    # ---- THE ACTUAL COUNTING (requirement #8) ----
                    # This only increments a count the FIRST time this
                    # exact track_id is ever seen. Every later frame the
                    # same object appears in is correctly ignored here.
                    is_new_object = counter.update(track_id, class_id)

                    # ---- ESP32 SORTING COMMAND (Phase 8: ESP32 comms) ----
                    # Only send a command the first time a NEW object is
                    # counted - never every frame. SORTING_COOLDOWN_SECONDS
                    # also throttles back-to-back sends so the physical
                    # sorter has time to act between commands.
                    if is_new_object:
                        now = time.time()
                        if now - last_sort_send_time >= SORTING_COOLDOWN_SECONDS:
                            send_to_esp32(class_name)
                            last_sort_send_time = now
                        else:
                            print(f"[INFO] Skipped sending '{class_name}' - "
                                  f"still within {SORTING_COOLDOWN_SECONDS}s sorting cooldown.")

                    draw_detection_box(
                        cv2, annotated_frame, x1, y1, x2, y2,
                        class_name, confidence, track_id, box_color,
                    )

            # ---------------------------------------------------------
            # Draw the live category-wise count panel (requirement #9).
            # ---------------------------------------------------------
            draw_count_panel(cv2, annotated_frame, counter)

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
                (annotated_frame.shape[1] - 150, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),  # red text
                2,
                cv2.LINE_AA,
            )

            draw_footer_hints(cv2, annotated_frame)

            # ---------------------------------------------------------
            # Show the annotated frame in a window with the required title.
            # ---------------------------------------------------------
            cv2.imshow(WINDOW_TITLE, annotated_frame)

            # Wait 1ms for a key press.
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q") or key == ord("Q"):
                print("[INFO] 'Q' pressed. Shutting down ...")
                break

            if key == ord("r") or key == ord("R"):
                counter.reset()
                print("[INFO] 'R' pressed. All counts have been reset to zero.")

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
        close_connection()

        final_counts = counter.get_counts()
        print("-" * 70)
        print("[INFO] Final waste counts for this session:")
        for class_name in COUNT_DISPLAY_ORDER:
            print(f"       {class_name}: {final_counts.get(class_name, 0)}")
        print(f"       Total: {counter.get_total()}")
        print("-" * 70)
        print("[INFO] Camera released and windows closed. Goodbye!")


if __name__ == "__main__":
    main()
