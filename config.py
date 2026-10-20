"""
Configuration manager for OmniScan OCR.
Handles saving and loading user preferences, language choices, and API keys.
"""
import os
import json

CONFIG_DIR = os.path.expanduser("~/.omniscan_ocr")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "engine": "local",          # "local" (EasyOCR) or "cloud" (Gemini Free Cloud)
    "language": "ur_en",        # "ur_en" (Urdu + English), "ar_en" (Arabic + English), "en" (English), "auto"
    "gemini_api_key": "",       # Free Google AI Studio API key (optional)
    "gemini_model": "gemini-2.5-flash",
    "auto_copy_clipboard": True,
    "play_sound": True,
    "floating_bar_visible": True,
    "hotkey": "Ctrl+Alt+S",
    "pdf_dpi": 200,             # DPI for PDF page rendering during OCR
    "history_limit": 50,
    "theme": "dark",            # "dark" or "light"
}

def load_config():
    """Load configuration from disk, creating defaults if not found."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Merge with defaults in case of missing keys
            config = DEFAULT_CONFIG.copy()
            config.update(data)
            return config
    except Exception as e:
        print(f"Error loading config: {e}. Using defaults.")
        return DEFAULT_CONFIG.copy()

def save_config(config_dict):
    """Save configuration dictionary to disk."""
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving config: {e}")
