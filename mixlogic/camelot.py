"""Camelot key notation, real-key mapping and harmonic compatibility rules."""
import re

# Each entry: perfect | boost_1 | boost_2 | boost_3 | drop_1 | drop_2 | drop_3 | mood
# Values are space-separated Camelot keys, taken from the original chart.
_CHART_TEXT = """
1A|1A 12B|1B 2A|10A|3A 8A|12A|4A|11A 6A|4B
2A|2A 1B|2B 3A|11A|4A 9A|1A|5A|12A 7A|5B
3A|3A 2B|3B 4A|12A|5A 10A|2A|6A|1A 8A|6B
4A|4A 3B|4B 5A|1A|6A 11A|3A|7A|2A 9A|7B
5A|5A 4B|5B 6A|2A|7A 12A|4A|8A|3A 10A|8B
6A|6A 5B|6B 7A|3A|8A 1A|5A|9A|4A 11A|9B
7A|7A 6B|7B 8A|4A|9A 2A|6A|10A|5A 12A|10B
8A|8A 7B|8B 9A|5A|10A 3A|7A|11A|6A 1A|11B
9A|9A 8B|9B 10A|6A|11A 4A|8A|12A|7A 2A|12B
10A|10A 9B|10B 11A|7A|12A 5A|9A|1A|8A 3A|1B
11A|11A 10B|11B 12A|8A|1A 6A|10A|2A|9A 4A|2B
12A|12A 11B|12B 1A|9A|2A 7A|11A|3A|10A 5A|3B
1B|1B 2A|2B|10B|3B 8B|1A 12B|4B|11B 6B|10A
2B|2B 3A|3B|11B|4B 9B|2A 1B|5B|12B 7B|11A
3B|3B 4A|4B|12B|5B 10B|3A 2B|6B|1B 8B|12A
4B|4B 5A|5B|1B|6B 11B|4A 3B|7B|2B 9B|1A
5B|5B 6A|6B|2B|7B 12B|5A 4B|8B|3B 10B|2A
6B|6B 7A|7B|3B|8B 1B|6A 5B|9B|4B 11B|3A
7B|7B 8A|8B|4B|9B 2B|7A 6B|10B|5B 12B|4A
8B|8B 9A|9B|5B|10B 3B|8A 7B|11B|6B 1B|5A
9B|9B 10A|10B|6B|11B 4B|9A 8B|12B|7B 2B|6A
10B|10B 11A|11B|7B|12B 5B|10A 9B|1B|8B 3B|7A
11B|11B 12A|12B|8B|1B 6B|11A 10B|2B|9B 4B|8A
12B|12B 1A|1B|9B|2B 7B|12A 11B|3B|10B 5B|9A
"""

_CATEGORIES = ("perfect", "boost_1", "boost_2", "boost_3",
               "drop_1", "drop_2", "drop_3", "mood")


def _build_chart():
    chart = {}
    for line in _CHART_TEXT.strip().splitlines():
        cols = line.split("|")
        key = cols[0]
        chart[key] = {cat: cols[i + 1].split() for i, cat in enumerate(_CATEGORIES)}
    return chart


EXTENDED_CAMELOT_CHART = _build_chart()

# Second reference grid, with its own relation names.
def _build_standard_chart():
    """Chart 2, built from the second supplied reference grid."""
    chart = {}
    for num in range(1, 13):
        for letter in ("A", "B"):
            other = "B" if letter == "A" else "A"

            def wrap(n):
                return (n - 1) % 12 + 1

            def same(n):
                return f"{wrap(n)}{letter}"

            def swap(n):
                return f"{wrap(n)}{other}"

            # Diagonal and mood use the other letter with different offsets for A and B.
            diag_off = -1 if letter == "A" else 1
            mood_off = 3 if letter == "A" else 9
            chart[f"{num}{letter}"] = {
                "perfect": [same(num)],
                "minus1": [same(num - 1)],
                "plus1": [same(num + 1)],
                "boost": [same(num + 2)],
                "scale": [swap(num)],
                "diagonal": [swap(num + diag_off)],
                "jaw": [same(num + 7)],
                "mood": [swap(num + mood_off)],
            }
    return chart


STANDARD_CAMELOT_CHART = _build_standard_chart()

# Name of the chart used by get_compatibility. Switched from the Options dialog.
CHART_CHOICES = {
    "Chart 1 (energy boost / drop)": EXTENDED_CAMELOT_CHART,
    "Chart 2 (harmonic transitions)": STANDARD_CAMELOT_CHART,
}
active_chart_name = next(iter(CHART_CHOICES))


def set_active_chart(name):
    global active_chart_name
    if name not in CHART_CHOICES and (str(name).startswith("Chart 2 ") or str(name).startswith("Chart B")):
        name = list(CHART_CHOICES)[1]
    if name in CHART_CHOICES:
        active_chart_name = name

# Wheel colours for each key (Camelot wheel palette used by the original app).
CAMELOT_COLORS = {
    "1A": "#70ECD4", "1B": "#00EDC9",
    "2A": "#92F0A4", "2B": "#27EC82",
    "3A": "#B1EE86", "3B": "#85ED4E",
    "4A": "#E6E0A2", "4B": "#E0C86E",
    "5A": "#FEC8AC", "5B": "#FFA279",
    "6A": "#FFB3BF", "6B": "#FF8C93",
    "7A": "#FFB4D2", "7B": "#FF85B4",
    "8A": "#EBB7F9", "8B": "#F087D9",
    "9A": "#E7B6F8", "9B": "#CE93FF",
    "10A": "#C0CEFB", "10B": "#A1B9FF",
    "11A": "#94E5F8", "11B": "#3ED2F8",
    "12A": "#50EBF0", "12B": "#50EBF0",
}

REAL_KEYS = {
    "1A": "Abm", "1B": "B", "2A": "Ebm", "2B": "F#", "3A": "Bbm", "3B": "Db",
    "4A": "Fm", "4B": "Ab", "5A": "Cm", "5B": "Eb", "6A": "Gm", "6B": "Bb",
    "7A": "Dm", "7B": "F", "8A": "Am", "8B": "C", "9A": "Em", "9B": "G",
    "10A": "Bm", "10B": "D", "11A": "F#m", "11B": "A", "12A": "Dbm", "12B": "E",
}

REAL_TO_CAMELOT = {
    "abm": "1A", "g#m": "1A", "b": "1B", "bmaj": "1B",
    "ebm": "2A", "d#m": "2A", "f#": "2B", "gb": "2B", "f#maj": "2B", "gbmaj": "2B",
    "bbm": "3A", "a#m": "3A", "db": "3B", "c#": "3B", "dbmaj": "3B", "c#maj": "3B",
    "fm": "4A", "ab": "4B", "g#": "4B", "abmaj": "4B", "g#maj": "4B",
    "cm": "5A", "eb": "5B", "d#": "5B", "ebmaj": "5B", "d#maj": "5B",
    "gm": "6A", "bb": "6B", "a#": "6B", "bbmaj": "6B", "a#maj": "6B",
    "dm": "7A", "f": "7B", "fmaj": "7B",
    "am": "8A", "c": "8B", "cmaj": "8B",
    "em": "9A", "g": "9B", "gmaj": "9B",
    "bm": "10A", "d": "10B", "dmaj": "10B",
    "f#m": "11A", "gbm": "11A", "a": "11B", "amaj": "11B",
    "dbm": "12A", "c#m": "12A", "e": "12B", "emaj": "12B",
    "amin": "8A", "bmin": "10A", "cmin": "5A", "dmin": "7A",
    "emin": "9A", "fmin": "4A", "gmin": "6A",
}

_CAMELOT_RE = re.compile(r"\b(1[0-2]|[1-9])[AB]\b")


def normalize_key(key_str):
    """Return a Camelot code such as '8A' for a Camelot or musical key string, or None."""
    if not key_str:
        return None
    cleaned = str(key_str).strip().replace(" ", "")
    upper = cleaned.upper()
    if upper in CAMELOT_COLORS:
        return upper
    lower = cleaned.lower()
    if lower in REAL_TO_CAMELOT:
        return REAL_TO_CAMELOT[lower]
    match = _CAMELOT_RE.search(upper)
    return match.group(0) if match else None


def camelot_sort_key(code):
    """Sort order for Camelot codes: 1A..12A then 1B..12B."""
    code = normalize_key(code)
    if code is None:
        return 99, "Z"
    return int(code[:-1]), code[-1]


# One colour per relation type, shared by the wheel, both tables and the Help tab.
# Each entry: (label, wheel/table colour, dark row tint for table backgrounds, description).
VARIATIONS = {
    "Perfect Match": ("#39FF88", (20, 74, 40), "Chart 1: the Perfect match column, including its cross-letter matches."),
    "Energy Boost (+)": ("#00E5FF", (14, 62, 72), "Chart 1: Energy boost + column."),
    "Energy Boost (++)": ("#2F9BFF", (18, 42, 80), "Chart 1: Energy boost ++ column (three numbers back, same letter)."),
    "Energy Boost (+++)": ("#7C5CFF", (48, 34, 84), "Chart 1: Energy boost +++ column, including the bracketed alternative."),
    "Energy Drop (-)": ("#FFD23F", (84, 70, 14), "Chart 1: Energy drop - column."),
    "Energy Drop (--)": ("#FF9A2E", (84, 52, 14), "Chart 1: Energy drop -- column (three numbers forward, same letter)."),
    "Energy Drop (---)": ("#FF4D5E", (84, 26, 30), "Chart 1: Energy drop --- column, including the bracketed alternative."),
    "Mood Change": ("#FF6FD8", (76, 22, 66), "Chart 1: Mood change column (A: three forward to B; B: three back to A)."),
    "Incompatible": ("#8A919E", (70, 22, 28), "Not harmonic. Expect a clash."),
    # Chart 2 column names (see _GRID_LABELS).
    "Perfect Mix": ("#39FF88", (20, 74, 40), "Chart 2: same key."),
    "-1 Mix": ("#FFD23F", (84, 70, 14), "Chart 2: one step down, same letter."),
    "+1 Mix": ("#FF9A2E", (84, 52, 14), "Chart 2: one step up, same letter."),
    "Energy Boost": ("#00E5FF", (14, 62, 72), "Chart 2: two steps up, same letter."),
    "Scale Change": ("#2F9BFF", (18, 42, 80), "Chart 2: same number, other letter."),
    "Diagonal Mix": ("#7C5CFF", (48, 34, 84), "Chart 2: one step, other letter."),
    "Jaw's Mix": ("#FF4D5E", (84, 26, 30), "Chart 2: seven steps up, same letter."),
    "Mood Shifter": ("#FF6FD8", (76, 22, 66), "Chart 2: a mood shift, other letter."),
}


def get_compatibility(key1, key2, chart_name=None):
    """Return (colour, label) describing how key2 mixes after key1.

    colour is one of: green (perfect/boost), orange (energy drop, boost++ or mood change),
    red (incompatible).
    """
    k1 = normalize_key(key1)
    k2 = normalize_key(key2)
    if k1 is None or k2 is None:
        return "unknown", "Unknown — key metadata unavailable"
    entry = CHART_CHOICES[chart_name or active_chart_name].get(k1)
    if entry is None:
        return "red", "Incompatible"
    if "minus1" in entry:
        return _get_grid_compatibility(entry, k2)
    if k2 in entry["perfect"]:
        return "green", "Perfect Match"
    if k2 in entry["boost_1"]:
        return "green", "Energy Boost (+)"
    if k2 in entry["boost_2"]:
        return "orange", "Energy Boost (++)"
    if k2 in entry["boost_3"]:
        return "orange", "Energy Boost (+++)"
    if k2 in entry["drop_1"]:
        return "orange", "Energy Drop (-)"
    if k2 in entry["drop_2"]:
        return "orange", "Energy Drop (--)"
    if k2 in entry["drop_3"]:
        return "orange", "Energy Drop (---)"
    if k2 in entry["mood"]:
        return "orange", "Mood Change"
    return "red", "Incompatible"


# Chart 2 uses the relation names from the second reference grid.
# Each entry: (column, row colour status, label).
_GRID_LABELS = [
    ("perfect", "green", "Perfect Mix"),
    ("minus1", "orange", "-1 Mix"),
    ("plus1", "orange", "+1 Mix"),
    ("boost", "green", "Energy Boost"),
    ("scale", "green", "Scale Change"),
    ("diagonal", "orange", "Diagonal Mix"),
    ("jaw", "orange", "Jaw's Mix"),
    ("mood", "orange", "Mood Shifter"),
]


def _get_grid_compatibility(entry, k2):
    for column, colour, label in _GRID_LABELS:
        if k2 in entry[column]:
            return colour, label
    return "red", "Incompatible"
