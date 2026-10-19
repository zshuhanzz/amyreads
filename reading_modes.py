"""
AmyReads - Reading Mode Selector Widget (helper, not used directly as separate file)
"""


class ReadingModeSelector:
    """
    Constants and helpers for reading modes.
    """
    MODES = [
        "Original",
        "High Contrast",
        "Line Focus",
        "Bionic Reading",
        "Clean Text",
    ]

    DESCRIPTIONS = {
        "Original": "Display the PDF normally with original formatting.",
        "High Contrast": "Improve text visibility. Supports light and dark themes.",
        "Line Focus": "Dim surrounding content; highlight the line under your cursor.",
        "Bionic Reading": "Bold the beginning of words to aid visual tracking.",
        "Clean Text": "Extract text into a distraction-free reading layout.",
    }
