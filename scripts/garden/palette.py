"""Color tokens for the light and dark gardens.

The light garden is a clear spring morning (pale sky over pink haze), the dark
one a spring night in indigo. Ramps run from the deepest shade (index 0) to
the palest (index 5).
"""

LIGHT = {
    "scheme": "light",
    "bg": ["#F2F7FF", "#FFF5F9"],
    "glow": "#FCDCE8",
    "glow2": "#DCE8FD",
    "bokeh": "#FFFFFF",
    "card": "#FBFCFF",
    "border": "#DFE5F6",
    "ink": "#2B2F63",
    "ink2": "#575D92",
    "ink3": "#979DC6",
    "kikyo": ["#3B3A9A", "#5451C0", "#7673DA", "#9FA1EC", "#C9CEF8", "#EDF0FE"],
    "sakura": ["#BF577F", "#DC86A6", "#EEB2C7", "#F7D2DF", "#FCEAF0", "#FFF8FB"],
    "lav": ["#4E2F8F", "#6C49B5", "#8E6CD6", "#B39AE8", "#D6C8F5", "#EEE7FC"],
    "rose": ["#A63E70", "#C9628F", "#E28EB2", "#F1B9D0", "#FADDE9", "#FFF1F6"],
    "peach": ["#D27257", "#EA9F83", "#F6C9B4", "#FCE2D6", "#FEF0E9", "#FFF8F4"],
    "cream": ["#FFFDF8", "#F3EAD9"],
    "gold": ["#C08A1E", "#E5B447", "#F5D98C"],
    "leaf": ["#3F6A4C", "#5E8B66", "#86AE86", "#B7D1AE"],
    "stem": "#5E7F5A",
    "bark": "#7B5B57",
    "vine": "#8A7A63",
    "wisp": "#9A9FE6",
}

DARK = {
    "scheme": "dark",
    "bg": ["#0F1431", "#1E1632"],
    "glow": "#3D2048",
    "glow2": "#1C2B5C",
    "bokeh": "#C9CEF8",
    "card": "#131833",
    "border": "#2A3259",
    "ink": "#EEF1FF",
    "ink2": "#B8BFEA",
    "ink3": "#7C84B6",
    "kikyo": ["#5856C6", "#7472DF", "#9696EE", "#BABCF6", "#D9DCFB", "#F0F2FE"],
    "sakura": ["#C25E8C", "#DD8AAE", "#EFB2CB", "#F7D2E0", "#FCE9F1", "#FFF6FA"],
    "lav": ["#6544B8", "#8261DA", "#A487EE", "#C4AFF7", "#DED2FB", "#F3EEFE"],
    "rose": ["#B24F86", "#D477A6", "#EA9DC2", "#F5C4DB", "#FBE0EE", "#FFF3F9"],
    "peach": ["#D97D60", "#EEA98D", "#F8D0BD", "#FCE4D9", "#FEF1EB", "#FFF8F5"],
    "cream": ["#FFF9EF", "#E9DDC6"],
    "gold": ["#D6A23A", "#F0C661", "#F8E09C"],
    "leaf": ["#3D6D4F", "#5A9167", "#80B585", "#B0D6AB"],
    "stem": "#6F9B6B",
    "bark": "#9A7A73",
    "vine": "#A08E75",
    "wisp": "#AEB4F4",
}

THEMES = {"light": LIGHT, "dark": DARK}
