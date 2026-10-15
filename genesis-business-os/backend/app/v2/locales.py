"""Shared saved-customer locale contract; API identifiers remain untranslated."""
from typing import Literal

Language = Literal["en", "es", "zh", "ar", "hi", "sw"]
LANGUAGES = [
    {"code": "en", "label": "English", "direction": "ltr"},
    {"code": "es", "label": "Español", "direction": "ltr"},
    {"code": "zh", "label": "中文（普通话）", "direction": "ltr"},
    {"code": "ar", "label": "العربية", "direction": "rtl"},
    {"code": "hi", "label": "हिन्दी", "direction": "ltr"},
    {"code": "sw", "label": "Kiswahili", "direction": "ltr"},
]
