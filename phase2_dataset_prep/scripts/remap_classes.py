"""
Phase 2 - Step 3: Filter + remap the dataset to exactly 3 classes.

    0 = Plastic
    1 = Organic
    2 = Metal

What this does, per split (train / valid / test):
1. Reads each YOLO label file (class_id x_center y_center width height,
   normalized 0-1, one box per line).
2. Looks up each original class_id's NAME (from raw_dataset's data.yaml),
   then looks up that name in class_map.CLASS_MAP.
3. Keeps only the boxes whose class maps to Plastic/Organic/Metal, and
   rewrites the class_id to the new 0/1/2 scheme.
4. If an image ends up with ZERO kept boxes, that image + its label file
   are EXCLUDED from the output dataset (no Plastic/Organic/Metal object
   is actually present in it, so it's not useful as a positive example
   for these 3 classes).
5. Copies the kept images + writes the new label files into:
       dataset_yolo/
       ├── data.yaml
       ├── train/images, train/labels
       ├── valid/images, valid/labels
       └── test/images,  test/labels
6. Prints a final per-class object count so you can see class balance
   before training (Organic will likely be the smallest class - see the
   note printed at the end).

This script does NOT do any training, augmentation, or resizing -
only filtering + relabeling + reorganizing.
"""

import shutil
import sys
from collections import Counter
from pathlib import Path
import os
import stat
import time

import yaml
from tqdm import tqdm

sys.path.append(str(Path(__file__).resolve().parent))
from class_map import CLASS_MAP, TARGET_CLASSES, TARGET_NAME_TO_ID  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "raw_dataset"
OUT_DIR = PROJECT_ROOT / "dataset_yolo"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def find_data_yaml(root: Path) -> Path:
    matches = sorted(root.rglob("data.yaml"), key=lambda p: len(p.parts))
    if not matches:
        raise FileNotFoundError(f"No data.yaml found under {root}")
    return matches[0]


def load_original_names(yaml_path: Path) -> list[str]:
    with open(yaml_path, "r", encoding="utf-8") as f:
        meta = yaml.safe_load(f)
    names = meta["names"]
    if isinstance(names, dict):
        names = [names[i] for i in sorted(names)]
    return names


def find_image_for_label(images_dir: Path, stem: str) -> Path | None:
    for ext in IMAGE_EXTS:
        candidate = images_dir / f"{stem}{ext}"
        if candidate.exists():
            return candidate
    return None


def process_split(split_dir: Path, out_split_dir: Path, orig_names: list[str],
                   counter: Counter) -> tuple[int, int]:
    images_dir = split_dir / "images"
    labels_dir = split_dir / "labels"
    image_files = [f for f in images_dir.iterdir() if f.is_file()
                   and f.suffix.lower() in IMAGE_EXTS] if images_dir.exists() else []
    label_files = sorted(labels_dir.glob("*.txt")) if labels_dir.exists() else []
    print(f"    {split_dir.name}: {len(image_files)} images, "
          f"{len(label_files)} label files")
    if not labels_dir.exists():
        return 0, 0

    out_images_dir = out_split_dir / "images"
    out_labels_dir = out_split_dir / "labels"
    out_images_dir.mkdir(parents=True, exist_ok=True)
    out_labels_dir.mkdir(parents=True, exist_ok=True)

    kept_images, skipped_images = 0, 0
    for label_path in tqdm(label_files, desc=f"  {split_dir.name}"):
        kept_lines = []
        for line in label_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            orig_id = int(parts[0])
            if orig_id >= len(orig_names):
                continue  # malformed label, skip defensively
            orig_name = orig_names[orig_id].strip().lower()
            target_name = CLASS_MAP.get(orig_name)
            if target_name is None:
                continue  # dropped class
            new_id = TARGET_NAME_TO_ID[target_name]
            kept_lines.append(f"{new_id} {' '.join(parts[1:])}")
            counter[target_name] += 1

        if not kept_lines:
            skipped_images += 1
            continue  # no Plastic/Organic/Metal object in this image

        image_path = find_image_for_label(images_dir, label_path.stem)
        if image_path is None:
            skipped_images += 1
            continue  # label exists but matching image is missing

        shutil.copy2(image_path, out_images_dir / image_path.name)
        (out_labels_dir / label_path.name).write_text(
            "\n".join(kept_lines) + "\n", encoding="utf-8"
        )
        kept_images += 1

    return kept_images, skipped_images


def main():
    yaml_path = find_data_yaml(RAW_DIR)
    dataset_root = yaml_path.parent
    orig_names = load_original_names(yaml_path)
    if not (dataset_root / "train" / "images").is_dir():
        metadata = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        source_train = str(metadata.get("train", "")).replace("\\", "/")
        source_root_name = source_train.rstrip("/").split("/")[-3]
        candidates = [
            path.parent for path in RAW_DIR.rglob("train")
            if path.name == "train"
            and path.parent.name == source_root_name
            and (path / "images").is_dir()
            and (path / "labels").is_dir()
        ]
        if len(candidates) == 1:
            dataset_root = candidates[0]
    print(f"Loaded {len(orig_names)} original classes from {yaml_path}\n")

    if OUT_DIR.exists():
        print(f"'{OUT_DIR}' already exists - removing old copy first.")

        def _on_rm_error(func, path, exc_info):
            """Error handler for shutil.rmtree to make removal Windows-safe.

            Attempts to make the file writable and retries a few times to handle
            transient Windows file locking. Falls back to os.remove/os.rmdir
            as a last resort and re-raises if still failing.
            """
            try:
                os.chmod(path, stat.S_IWRITE)
            except Exception:
                pass
            try:
                func(path)
                return
            except Exception:
                # Retry a few times (short sleeps) in case another process
                # briefly held the file open.
                for _ in range(5):
                    time.sleep(0.2)
                    try:
                        func(path)
                        return
                    except Exception:
                        continue
                # Final attempts: try direct remove/rmdir, then re-raise
                try:
                    if os.path.isdir(path):
                        os.rmdir(path)
                    else:
                        os.remove(path)
                    return
                except Exception:
                    raise

            for attempt in range(5):
                try:
                    shutil.rmtree(OUT_DIR, onerror=_on_rm_error)
                    break
                except OSError:
                    if attempt == 4:
                        raise
                    time.sleep(0.2)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    counter: Counter = Counter()
    split_map = {"train": "train", "valid": "valid", "val": "valid", "test": "test"}
    seen_out_splits = set()

    print("Filtering + remapping labels:")
    for split_key, out_key in split_map.items():
        split_dir = dataset_root / split_key
        if not split_dir.exists() or out_key in seen_out_splits:
            continue
        seen_out_splits.add(out_key)
        kept, skipped = process_split(split_dir, OUT_DIR / out_key, orig_names, counter)
        print(f"    {split_key:6s}-> kept {kept} images, skipped {skipped} "
              f"(no target-class object / missing image)")

    # Write the new data.yaml for the 3-class dataset
    new_yaml = {
        "path": str(OUT_DIR),
        "train": "train/images",
        "val": "valid/images" if (OUT_DIR / "valid").exists() else "train/images",
        "test": "test/images" if (OUT_DIR / "test").exists() else "",
        "nc": len(TARGET_CLASSES),
        "names": TARGET_CLASSES,
    }
    with open(OUT_DIR / "data.yaml", "w", encoding="utf-8") as f:
        yaml.dump(new_yaml, f, sort_keys=False)

    print(f"\nWrote final dataset to: {OUT_DIR}")
    print(f"Wrote data.yaml: {OUT_DIR / 'data.yaml'}\n")

    print("Final object counts per class (across all splits):")
    total = sum(counter.values())
    for name in TARGET_CLASSES:
        n = counter.get(name, 0)
        pct = (100 * n / total) if total else 0
        print(f"  {name:8s} (id {TARGET_NAME_TO_ID[name]}): {n:6d} objects  ({pct:.1f}%)")

    smallest = min(counter, key=lambda k: counter.get(k, 0)) if counter else None
    if smallest and total and counter[smallest] / total < 0.15:
        print(
            f"\nNote: '{smallest}' is under-represented ({counter[smallest]} objects, "
            f"{100 * counter[smallest] / total:.1f}% of the total). This is common - "
            "the source dataset only had one original class ('Organic') covering this "
            "category. Consider one of, before training:\n"
            "  - class-weighted loss / more aggressive augmentation for that class, or\n"
            "  - adding a second Kaggle organic-waste-detection dataset and merging it "
            "in (same 0/1/2 id scheme) before training.\n"
            "This script only prepares data - no training happens here."
        )


if __name__ == "__main__":
    main()
