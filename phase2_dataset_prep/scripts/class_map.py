"""
Original -> Target class mapping.

Target classes (fixed, required order/ids):
    0 = Plastic
    1 = Organic
    2 = Metal

CLASS_MAP keys are the ORIGINAL class names from the Kaggle dataset's
data.yaml, lowercased. Values are which target class each maps to.
Any original class NOT listed here is DROPPED (its labels are removed,
and images that end up with zero remaining boxes are excluded from the
remapped dataset - see remap_classes.py).

The source dataset ("Waste Classification - YOLOv8 dataset",
https://www.kaggle.com/datasets/spellsharp/garbage-data) has 44 classes.
Only classes that are UNAMBIGUOUSLY plastic / organic / metal are mapped.
Ambiguous / mixed-material classes (e.g. "Foil", "Milk bottle", "Ramen
Cup", "Food Packet", "Disposable tableware", "Cellulose") are deliberately
left out rather than guessed - remapping them wrong would poison training
labels. If you inspect the data and are confident about one of these,
just add a line for it below.
"""

TARGET_CLASSES = ["Plastic", "Organic", "Metal"]  # index 0, 1, 2 - fixed order

CLASS_MAP: dict[str, str] = {
    # ---- Plastic (-> 0) ----
    "combined plastic": "Plastic",
    "plastic bag": "Plastic",
    "plastic bottle": "Plastic",
    "plastic can": "Plastic",
    "plastic canister": "Plastic",
    "plastic caps": "Plastic",
    "plastic cup": "Plastic",
    "plastic shaker": "Plastic",
    "plastic shavings": "Plastic",
    "plastic toys": "Plastic",
    "unknown plastic": "Plastic",
    "zip plastic bag": "Plastic",
    "stretch film": "Plastic",

    # ---- Organic (-> 1) ----
    "organic": "Organic",

    # ---- Metal (-> 2) ----
    "aluminum can": "Metal",
    "aluminum caps": "Metal",
    "iron utensils": "Metal",
    "metal shavings": "Metal",
    "scrap metal": "Metal",
    "tin": "Metal",

    # Everything else (Aerosols, Cardboard, Cellulose, Ceramic, Container
    # for household chemicals, Disposable tableware, Electronics, Foil,
    # Furniture, Glass bottle, Liquid, Milk bottle, Paper bag, Paper cups,
    # Paper shavings, Paper, Papier mache, Postal packaging, Printing
    # industry, Tetra pack, Textile, Wood, Ramen Cup, Food Packet)
    # is intentionally left unmapped -> dropped.
}

TARGET_NAME_TO_ID = {name: i for i, name in enumerate(TARGET_CLASSES)}
