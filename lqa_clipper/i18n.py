import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

_LOCALES_DIR = Path(__file__).parent / "locales"
_TRANSLATIONS: Dict[str, Dict[str, str]] = {}

# Language code to Display Name mapping
_LANG_NAMES = {
    "ja": "日本語",
    "en": "English",
    "zh": "中文",
}


def load_all_locales() -> Dict[str, Dict[str, str]]:
    """Load all JSON files from the locales directory."""
    global _TRANSLATIONS
    if not _TRANSLATIONS:
        if _LOCALES_DIR.exists():
            for json_file in _LOCALES_DIR.glob("*.json"):
                lang_code = json_file.stem
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        _TRANSLATIONS[lang_code] = json.load(f)
                except Exception as e:
                    print(f"Failed to load locale {json_file}: {e}")
    return _TRANSLATIONS


def get_locale(lang_code: str = "ja") -> Dict[str, str]:
    """Get translation dictionary for the specified language code (fallback to 'ja')."""
    locales = load_all_locales()
    if lang_code in locales:
        return locales[lang_code]
    return locales.get("ja", {})


def get_language_choices() -> List[Tuple[str, str]]:
    """Get list of (Display Name, Language Code) tuples for Gradio dropdown."""
    locales = load_all_locales()
    choices = []
    for code in ("ja", "en", "zh"):
        if code in locales:
            name = _LANG_NAMES.get(code, code)
            choices.append((name, code))
    # Any other custom languages
    for code in locales:
        if code not in ("ja", "en", "zh"):
            choices.append((code, code))
    return choices
