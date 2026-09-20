"""
Phase 2 - Step 1: Download the Kaggle dataset.

Dataset : "Waste Classification - YOLOv8 dataset"
Kaggle  : https://www.kaggle.com/datasets/spellsharp/garbage-data
Source  : Roboflow project "yolo-waste-detection" by projectverba
          (https://universe.roboflow.com/projectverba/yolo-waste-detection)
License : CC BY 4.0

Why this dataset:
- It is already an OBJECT DETECTION dataset (bounding boxes), not a plain
  classification dataset -> directly usable for YOLO.
- It ships in YOLO format already (images/ + labels/ + data.yaml), so no
  format conversion is needed (e.g. from COCO/VOC).
- It has 44 fine-grained classes, and a large chunk of them map cleanly
  and safely onto our 3 target classes: Plastic, Organic, Metal.

--------------------------------------------------------------------------
HOW TO DOWNLOAD
--------------------------------------------------------------------------
Option A (this script, recommended) - uses `kagglehub`:
    1. pip install -r requirements.txt
    2. Get a Kaggle API token:
         Kaggle website -> profile picture -> Settings -> API ->
         "Create New Token" -> downloads kaggle.json
    3. Place kaggle.json at:
         Windows: C:\\Users\\<you>\\.kaggle\\kaggle.json
         Linux/Mac: ~/.kaggle/kaggle.json
    4. Run:
         python scripts/download_dataset.py

Option B (manual, no code):
    1. Go to https://www.kaggle.com/datasets/spellsharp/garbage-data
    2. Click "Download" (top right) -> downloads a .zip
    3. Extract it into: waste_dataset_prep/raw_dataset/

Either way, after this step you should have a folder that contains
(paths inside the zip can be nested one level deeper - the inspect
script in step 2 will locate the real root automatically):

    raw_dataset/
    ├── data.yaml
    ├── train/
    │   ├── images/
    │   └── labels/
    ├── valid/
    │   ├── images/
    │   └── labels/
    └── test/
        ├── images/
        └── labels/
--------------------------------------------------------------------------
"""

import shutil
from pathlib import Path

KAGGLE_DATASET_ID = "spellsharp/garbage-data"
TARGET_DIR = Path(__file__).resolve().parent.parent / "raw_dataset"


def download_with_kagglehub() -> Path:
    import kagglehub

    print(f"Downloading '{KAGGLE_DATASET_ID}' from Kaggle via kagglehub ...")
    cached_path = kagglehub.dataset_download(KAGGLE_DATASET_ID)
    cached_path = Path(cached_path)
    print(f"Downloaded to kagglehub cache: {cached_path}")

    TARGET_DIR.parent.mkdir(parents=True, exist_ok=True)
    if TARGET_DIR.exists():
        print(f"'{TARGET_DIR}' already exists - removing old copy first.")
        shutil.rmtree(TARGET_DIR)

    shutil.copytree(cached_path, TARGET_DIR)
    print(f"Copied dataset into project folder: {TARGET_DIR}")
    return TARGET_DIR


if __name__ == "__main__":
    try:
        path = download_with_kagglehub()
        print("\nDone. Dataset is ready at:", path)
        print("Next step: python scripts/inspect_classes.py")
    except Exception as e:
        print("\nAutomatic download failed with error:")
        print(f"   {e}")
        print(
            "\nFall back to the manual download (see the docstring at the top "
            "of this file, 'Option B'), then place the extracted dataset at:\n"
            f"   {TARGET_DIR}\n"
        )
