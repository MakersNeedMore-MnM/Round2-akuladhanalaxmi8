"""
AI Smart Drainage - Phase 3: YOLO Model Training
==================================================

This script trains a YOLO11 object detection model on the custom waste
dataset prepared in Phase 2 (Plastic / Organic / Metal).

It is written to be beginner-friendly and safe to run on a normal laptop:
- Automatically uses GPU (CUDA) if available, otherwise falls back to CPU.
- Uses automatic batch sizing on GPU, and a small safe batch size on CPU.
- Validates the dataset folder structure and data.yaml BEFORE training
  starts, so you get clear error messages instead of a crash halfway
  through.
- Catches common failure modes (missing packages, missing dataset,
  missing labels, invalid class ids, CUDA errors, out-of-memory errors)
  and prints a friendly explanation of how to fix them.

This script does NOT do webcam detection, counting, or any hardware
(ESP32 / servo) integration. It only trains the model. That comes later.

Usage:
    python train.py

(Normally you will not run this directly - use run_train.bat instead,
which sets up a virtual environment and installs requirements for you.)
"""

import os
import sys

# ---------------------------------------------------------------------------
# STEP 0: Basic settings
# ---------------------------------------------------------------------------
# These are intentionally simple, fixed values suitable for a beginner
# running this on a normal laptop (CPU or a modest GPU).

DATASET_YAML = os.path.join(
    "..", "phase2_dataset_prep", "dataset_yolo", "data.yaml"
)
DATASET_ROOT = os.path.join("..", "phase2_dataset_prep", "dataset_yolo")

PRETRAINED_MODEL = "yolo11n.pt"   # smallest / fastest YOLO11 model
EPOCHS = 3
IMG_SIZE = 416
PROJECT_DIR = "runs"              # all results saved under phase3_model_training/runs
RUN_NAME = "waste_yolo11n"

# The final classes must remain exactly these, in this order.
EXPECTED_CLASSES = {
    0: "Plastic",
    1: "Organic",
    2: "Metal",
}


# ---------------------------------------------------------------------------
# STEP 1: Friendly import check
# ---------------------------------------------------------------------------
# We check for required packages ourselves first, so that a missing
# package produces a clear one-line message instead of a raw Python
# traceback that confuses a beginner.

def check_required_packages():
    missing = []

    try:
        import torch  # noqa: F401
    except ImportError:
        missing.append("torch")

    try:
        import ultralytics  # noqa: F401
    except ImportError:
        missing.append("ultralytics")

    try:
        import yaml  # noqa: F401
    except ImportError:
        missing.append("pyyaml")

    if missing:
        print("=" * 70)
        print("ERROR: Missing required Python package(s): " + ", ".join(missing))
        print("=" * 70)
        print("Please install the requirements first by running:")
        print("    pip install -r requirements.txt")
        print()
        print("If you are using run_train.bat, this should happen")
        print("automatically. Try deleting the 'venv' folder and running")
        print("run_train.bat again.")
        sys.exit(1)


check_required_packages()

# It is now safe to import these, because check_required_packages()
# already confirmed they exist.
import torch                      # noqa: E402
import yaml                       # noqa: E402
from ultralytics import YOLO      # noqa: E402


# ---------------------------------------------------------------------------
# STEP 2: Dataset validation helpers
# ---------------------------------------------------------------------------

def fail(message):
    """Print a clear error banner and stop the script."""
    print("=" * 70)
    print("ERROR: " + message)
    print("=" * 70)
    sys.exit(1)


def check_dataset_folder_exists():
    if not os.path.isdir(DATASET_ROOT):
        fail(
            "Dataset folder not found at:\n"
            f"    {os.path.abspath(DATASET_ROOT)}\n\n"
            "Make sure Phase 2 has been completed and that the folder\n"
            "'phase2_dataset_prep/dataset_yolo/' exists next to\n"
            "'phase3_model_training/'."
        )


def check_data_yaml_exists():
    if not os.path.isfile(DATASET_YAML):
        fail(
            "data.yaml not found at:\n"
            f"    {os.path.abspath(DATASET_YAML)}\n\n"
            "Make sure Phase 2 finished successfully and produced\n"
            "'dataset_yolo/data.yaml'."
        )


def load_and_check_data_yaml():
    try:
        with open(DATASET_YAML, "r") as f:
            data_cfg = yaml.safe_load(f)
    except Exception as e:
        fail(f"Could not read data.yaml. Details: {e}")

    if not data_cfg or "names" not in data_cfg:
        fail(
            "data.yaml is missing a 'names' section listing the classes.\n"
            "Please re-check Phase 2 output."
        )

    names = data_cfg["names"]

    # names can be a list or a dict depending on how it was written
    if isinstance(names, list):
        names_dict = {i: n for i, n in enumerate(names)}
    elif isinstance(names, dict):
        names_dict = {int(k): v for k, v in names.items()}
    else:
        fail("data.yaml 'names' field has an unexpected format.")

    # Validate the class ids and names match exactly what is required
    if names_dict != EXPECTED_CLASSES:
        fail(
            "data.yaml classes do not match the required classes.\n"
            f"    Expected: {EXPECTED_CLASSES}\n"
            f"    Found:    {names_dict}\n\n"
            "Please re-check Phase 2's class remapping step."
        )

    print(f"[OK] data.yaml classes verified: {names_dict}")
    return data_cfg


def check_split_folder(split_name):
    """
    Checks that train/valid/test have both an images/ and labels/ folder,
    that images exist, that every image has a matching label file, and
    that every label file only contains valid class ids (0, 1, 2).
    Missing labels are only a hard error for train/valid (test labels
    are optional in many YOLO datasets), but we warn either way.
    """
    split_dir = os.path.join(DATASET_ROOT, split_name)
    images_dir = os.path.join(split_dir, "images")
    labels_dir = os.path.join(split_dir, "labels")

    if not os.path.isdir(split_dir):
        # test/ is sometimes optional, but train/ and valid/ are not.
        if split_name in ("train", "valid"):
            fail(f"Missing required dataset split folder: '{split_dir}'")
        else:
            print(f"[INFO] Optional split '{split_name}' not found, skipping.")
            return

    if not os.path.isdir(images_dir):
        fail(f"Missing images folder: '{images_dir}'")
    if not os.path.isdir(labels_dir):
        fail(f"Missing labels folder: '{labels_dir}'")

    valid_ext = (".jpg", ".jpeg", ".png", ".bmp", ".webp")
    image_files = [f for f in os.listdir(images_dir) if f.lower().endswith(valid_ext)]

    if len(image_files) == 0:
        fail(
            f"No images found in '{images_dir}'.\n"
            "Make sure Phase 2 copied images correctly."
        )

    missing_labels = []
    invalid_class_lines = []

    for img_file in image_files:
        base_name = os.path.splitext(img_file)[0]
        label_path = os.path.join(labels_dir, base_name + ".txt")

        if not os.path.isfile(label_path):
            missing_labels.append(img_file)
            continue

        # Validate class ids inside the label file
        try:
            with open(label_path, "r") as lf:
                for line_num, line in enumerate(lf, start=1):
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split()
                    class_id_str = parts[0]
                    if not class_id_str.lstrip("-").isdigit():
                        invalid_class_lines.append(
                            f"{label_path} (line {line_num}): '{class_id_str}' is not an integer"
                        )
                        continue
                    class_id = int(class_id_str)
                    if class_id not in EXPECTED_CLASSES:
                        invalid_class_lines.append(
                            f"{label_path} (line {line_num}): invalid class id {class_id}"
                        )
        except Exception as e:
            fail(f"Could not read label file '{label_path}'. Details: {e}")

    if missing_labels:
        preview = ", ".join(missing_labels[:5])
        more = "" if len(missing_labels) <= 5 else f" (+{len(missing_labels) - 5} more)"
        fail(
            f"{len(missing_labels)} image(s) in '{split_name}/images' have no "
            f"matching label file in '{split_name}/labels'.\n"
            f"Examples: {preview}{more}\n\n"
            "Every image must have a matching .txt label file with the same name."
        )

    if invalid_class_lines:
        preview = "\n    ".join(invalid_class_lines[:10])
        more = "" if len(invalid_class_lines) <= 10 else f"\n    (+{len(invalid_class_lines) - 10} more)"
        fail(
            "Invalid class id(s) found in label files. Only 0 (Plastic), "
            "1 (Organic), and 2 (Metal) are allowed:\n"
            f"    {preview}{more}"
        )

    print(f"[OK] '{split_name}' split verified: {len(image_files)} images, labels present, class ids valid.")


def validate_dataset():
    print("Checking dataset...")
    check_dataset_folder_exists()
    check_data_yaml_exists()
    load_and_check_data_yaml()

    for split in ("train", "valid", "test"):
        check_split_folder(split)

    print("Dataset check complete. Everything looks good.\n")


# ---------------------------------------------------------------------------
# STEP 3: Device selection (GPU if available, otherwise CPU)
# ---------------------------------------------------------------------------

def select_device_and_batch():
    """
    Returns (device, batch) to pass into YOLO's train().

    - If a CUDA GPU is available: device='0', batch=-1 (Ultralytics will
      automatically pick a safe batch size for the available GPU memory).
    - If not: device='cpu', batch=8 (a small, CPU-safe fixed batch size).
    """
    try:
        cuda_available = torch.cuda.is_available()
    except Exception as e:
        print(f"[WARNING] Could not check CUDA availability ({e}). Falling back to CPU.")
        cuda_available = False

    if cuda_available:
        gpu_name = torch.cuda.get_device_name(0)
        print(f"[OK] CUDA GPU detected: {gpu_name}")
        print("Using GPU for training with automatic batch size selection.")
        return "0", -1  # -1 = Ultralytics auto batch sizing
    else:
        print("[INFO] No CUDA-capable GPU detected.")
        print("Training will run on CPU using a small, safe batch size (8).")
        print("This will be slower than GPU training - that is expected on a laptop.")
        return "cpu", 8


# ---------------------------------------------------------------------------
# STEP 4: Training
# ---------------------------------------------------------------------------

def run_training():
    device, batch = select_device_and_batch()

    print("\nStarting training with the following settings:")
    print(f"    Base model : {PRETRAINED_MODEL}")
    print(f"    Data       : {DATASET_YAML}")
    print(f"    Epochs     : {EPOCHS}")
    print(f"    Image size : {IMG_SIZE}")
    print(f"    Device     : {device}")
    print(f"    Batch      : {'auto' if batch == -1 else batch}")
    print(f"    Results    : {os.path.abspath(PROJECT_DIR)}\n")

    try:
        model = YOLO(PRETRAINED_MODEL)
    except Exception as e:
        fail(
            f"Could not load the pretrained model '{PRETRAINED_MODEL}'.\n"
            "Ultralytics will normally download this automatically the "
            "first time you run training - make sure you are connected "
            f"to the internet.\nDetails: {e}"
        )

    try:
        model.train(
            data=DATASET_YAML,
            epochs=EPOCHS,
            imgsz=IMG_SIZE,
            batch=batch,
            device=device,
            project=PROJECT_DIR,
            name=RUN_NAME,
            exist_ok=True,
        )
    except torch.cuda.OutOfMemoryError:
        fail(
            "Out of GPU memory (CUDA out of memory) during training.\n\n"
            "How to fix this:\n"
            "  1. Open train.py and lower IMG_SIZE (e.g. from 640 to 416).\n"
            "  2. Or set a smaller fixed batch size instead of automatic "
            "batch sizing (e.g. batch=4) in select_device_and_batch().\n"
            "  3. Close other programs that are using GPU memory.\n"
            "  4. As a last resort, train on CPU (slower, but always works)."
        )
    except RuntimeError as e:
        msg = str(e).lower()
        if "out of memory" in msg:
            fail(
                "Out of memory during training (CPU or GPU).\n\n"
                "How to fix this:\n"
                "  1. Lower IMG_SIZE in train.py (e.g. from 640 to 416).\n"
                "  2. Lower the batch size (e.g. batch=4).\n"
                "  3. Close other programs to free up memory.\n"
                f"\nOriginal error: {e}"
            )
        elif "cuda" in msg:
            fail(
                "A CUDA-related error occurred during training.\n"
                "This usually means CUDA/GPU drivers are not set up "
                "correctly. The script will still work on CPU - try "
                "again, and if the problem repeats, it will fall back "
                f"to CPU automatically.\n\nOriginal error: {e}"
            )
        else:
            fail(f"Training failed with an unexpected error.\nDetails: {e}")
    except KeyboardInterrupt:
        print("\n[INFO] Training was interrupted by the user (Ctrl+C).")
        sys.exit(1)
    except Exception as e:
        fail(f"Training failed with an unexpected error.\nDetails: {e}")

    # ------------------------------------------------------------------
    # STEP 5: Report where the final model was saved
    # ------------------------------------------------------------------
    best_model_path = os.path.join(PROJECT_DIR, RUN_NAME, "weights", "best.pt")

    print("\n" + "=" * 70)
    if os.path.isfile(best_model_path):
        print("TRAINING COMPLETE")
        print("=" * 70)
        print(f"Final trained model (best.pt) saved at:\n    {os.path.abspath(best_model_path)}")
    else:
        print("Training finished, but best.pt was not found where expected.")
        print(f"Please check inside:\n    {os.path.abspath(os.path.join(PROJECT_DIR, RUN_NAME, 'weights'))}")
    print("=" * 70)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("AI Smart Drainage - Phase 3: YOLO11 Model Training")
    print("=" * 70)
    print()

    validate_dataset()
    run_training()
