"""
Phase 2 - Step 2: Inspect the downloaded dataset.

This script:
1. Finds the real dataset root (handles the extra nested folder Kaggle
   zips sometimes have).
2. Loads data.yaml and prints the ORIGINAL class list with their ids.
3. Counts how many image/label files exist per split.
4. Cross-checks every class name against class_map.py so you can see,
   before remapping, exactly which original classes will become
   Plastic / Organic / Metal, and which will be dropped.

Run this BEFORE remap_classes.py to sanity-check the dataset.
"""

import sys
from pathlib import Path

import yaml

sys.path.append(str(Path(__file__).resolve().parent))
from class_map import CLASS_MAP, TARGET_CLASSES  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "raw_dataset"


def find_data_yaml(root: Path) -> Path:
    matches = list(root.rglob("data.yaml"))
    if not matches:
        raise FileNotFoundError(
            f"No data.yaml found under {root}. "
            "Did you run download_dataset.py (or extract the manual zip) first?"
        )
    # If there are several (e.g. nested duplicate folders), take the shallowest one.
    matches.sort(key=lambda p: len(p.parts))
    return matches[0]


def count_files(split_dir: Path) -> tuple[int, int]:
    img_dir = split_dir / "images"
    lbl_dir = split_dir / "labels"
    n_img = len(list(img_dir.glob("*"))) if img_dir.exists() else 0
    n_lbl = len(list(lbl_dir.glob("*.txt"))) if lbl_dir.exists() else 0
    return n_img, n_lbl


def main():
    if not RAW_DIR.exists():
        raise FileNotFoundError(
            f"'{RAW_DIR}' does not exist yet. Run scripts/download_dataset.py first, "
            "or manually extract the Kaggle zip there."
        )

    yaml_path = find_data_yaml(RAW_DIR)
    dataset_root = yaml_path.parent
    print(f"Found data.yaml at: {yaml_path}")
    print(f"Dataset root: {dataset_root}\n")

    with open(yaml_path, "r", encoding="utf-8") as f:
        meta = yaml.safe_load(f)

    names = meta.get("names")
    if isinstance(names, dict):
        # some data.yaml files store names as {0: 'x', 1: 'y', ...}
        names = [names[i] for i in sorted(names)]

    print(f"Original number of classes (nc): {meta.get('nc', len(names))}")
    print("Original classes:")
    for idx, name in enumerate(names):
        print(f"  {idx:2d}: {name}")

    print("\nSplit file counts (images / label files):")
    for split_key in ("train", "val", "valid", "test"):
        split_dir = dataset_root / split_key
        if split_dir.exists():
            n_img, n_lbl = count_files(split_dir)
            print(f"  {split_key:6s}: {n_img} images, {n_lbl} label files")

    print("\nClass remap preview (original -> target):")
    kept, dropped = [], []
    for idx, name in enumerate(names):
        target = CLASS_MAP.get(name.strip().lower())
        if target is not None:
            kept.append((idx, name, target))
        else:
            dropped.append((idx, name))

    print(f"\n  KEEP ({len(kept)} original classes -> {len(TARGET_CLASSES)} target classes):")
    for idx, name, target in kept:
        print(f"    [{idx:2d}] {name:35s} -> {target}")

    print(f"\n  DROP ({len(dropped)} original classes, no safe mapping to our 3 targets):")
    for idx, name in dropped:
        print(f"    [{idx:2d}] {name}")

    print(
        "\nIf this mapping looks right, run: python scripts/remap_classes.py\n"
        "If a class in the DROP list should actually be kept (or a KEEP looks "
        "wrong for your use case), edit class_map.py first."
    )


if __name__ == "__main__":
    main()
