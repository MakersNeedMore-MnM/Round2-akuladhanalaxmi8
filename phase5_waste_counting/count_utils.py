"""
AI-Based Smart Drainage Waste Detection and Automatic Segregation System
--------------------------------------------------------------------------
PHASE 5: Category-wise Waste Counting - helper module

This module contains ONLY the counting logic, kept separate from main.py
so the counting rules are easy to read, test, and reuse.

CORE IDEA
---------
YOLO tracking (model.track(...)) assigns each physical object a
"tracking ID" that stays the same across frames as long as the object
stays visible / trackable. A single object sitting in front of the
camera will appear in MANY frames, so we must NOT count it once per
frame - we must count it only the FIRST time we ever see that
tracking ID.

The TrackCounter class below simply remembers every tracking ID it has
already counted (per class) and ignores any ID it has seen before.
"""

from collections import defaultdict


class TrackCounter:
    """
    Keeps category-wise (class-wise) counts of unique tracked objects.

    Each physical object gets one persistent tracking ID from YOLO's
    tracker (e.g. ByteTrack). This class makes sure that ID only ever
    increments the count ONCE, no matter how many frames that same
    object appears in.
    """

    def __init__(self, class_names: dict):
        """
        class_names: dict mapping class_id -> class_name, e.g.
                     {0: "Plastic", 1: "Organic", 2: "Metal"}
        """
        self.class_names = class_names

        # counts[class_name] -> integer count of unique objects seen so far.
        self.counts = defaultdict(int)
        for name in class_names.values():
            self.counts[name] = 0

        # Every tracking ID we have ALREADY counted, so we never count
        # the same physical object twice. This is the key to satisfying
        # requirement #4 and #5 (no repeated counting, one count per ID).
        self._counted_track_ids = set()

    def update(self, track_id, class_id):
        """
        Register one detection: a specific tracking ID belonging to a
        specific class, seen in the CURRENT frame.

        If this tracking ID has never been counted before, it is counted
        now (count for that class goes up by 1) and remembered so it is
        never counted again. If it HAS been counted before, nothing
        happens - this is what stops the same object being counted in
        every single frame it appears in.

        Returns True if this call resulted in a NEW count, False if the
        track_id was already counted before (i.e. this frame's sighting
        was ignored for counting purposes).
        """
        if track_id is None:
            # No tracking ID available (tracker hasn't assigned one yet,
            # or tracking failed for this detection) - we deliberately do
            # NOT count objects without a tracking ID, otherwise the same
            # object could be counted repeatedly every frame.
            return False

        if track_id in self._counted_track_ids:
            # Already counted this exact object before - skip it.
            return False

        # First time we've ever seen this tracking ID - count it once.
        class_name = self.class_names.get(class_id, f"Class {class_id}")
        self.counts[class_name] += 1
        self._counted_track_ids.add(track_id)
        return True

    def reset(self):
        """
        Reset all counts back to zero and forget every tracking ID that
        was counted so far. Used when the user presses 'R'.

        NOTE: This only resets the on-screen counters. It does NOT stop
        the YOLO tracker itself, so already-visible objects will keep
        their same tracking IDs - but since we've forgotten that we
        counted them, they WILL be counted again after a reset. This is
        the expected/intuitive behavior of a "reset counts" button.
        """
        for name in self.class_names.values():
            self.counts[name] = 0
        self._counted_track_ids.clear()

    def get_counts(self) -> dict:
        """Return a plain dict of {class_name: count}."""
        return dict(self.counts)

    def get_total(self) -> int:
        """Return the total number of unique objects counted so far."""
        return sum(self.counts.values())
