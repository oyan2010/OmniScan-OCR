"""
Unified OCR Engine for OmniScan OCR.
Supports:
1. Local Offline Engine (EasyOCR) - Urdu, Arabic, English, Persian, Hindi, etc.
2. Free Cloud AI Engine (Google Gemini Vision) - High-fidelity Nastaliq handwriting and complex layout recognition.
3. Native PDF fast text extractor (PyMuPDF).
"""
import os
import io
import base64
import requests
import numpy as np
from PIL import Image

# Language mappings for EasyOCR
LANG_CONFIGS = {
    "ur_en": {
        "name": "Urdu + English",
        "easyocr_langs": ["ur", "en"],
        "is_rtl": True,
        "direction": "rtl"
    },
    "ar_en": {
        "name": "Arabic + English",
        "easyocr_langs": ["ar", "en"],
        "is_rtl": True,
        "direction": "rtl"
    },
    "en": {
        "name": "English Only",
        "easyocr_langs": ["en"],
        "is_rtl": False,
        "direction": "ltr"
    },
    "fa_en": {
        "name": "Persian (Farsi) + English",
        "easyocr_langs": ["fa", "en"],
        "is_rtl": True,
        "direction": "rtl"
    },
    "hi_en": {
        "name": "Hindi + English",
        "easyocr_langs": ["hi", "en"],
        "is_rtl": False,
        "direction": "ltr"
    },
}

# Cache for EasyOCR reader instances to avoid re-allocating memory and reload time
_readers = {}

def get_easyocr_reader(lang_key="ur_en"):
    """Get or initialize cached EasyOCR reader."""
    global _readers
    import easyocr
    if lang_key not in LANG_CONFIGS:
        lang_key = "ur_en"
    
    langs = LANG_CONFIGS[lang_key]["easyocr_langs"]
    cache_key = "_".join(langs)
    
    if cache_key not in _readers:
        # Check GPU availability, fallback to CPU
        _readers[cache_key] = easyocr.Reader(langs, gpu=False)
    
    return _readers[cache_key]

def image_to_numpy(image_input):
    """Convert PIL Image, file path, or bytes to numpy array (RGB)."""
    if isinstance(image_input, np.ndarray):
        return image_input
    elif isinstance(image_input, Image.Image):
        return np.array(image_input.convert("RGB"))
    elif isinstance(image_input, str):
        if not os.path.exists(image_input):
            raise FileNotFoundError(f"Image file not found: {image_input}")
        with Image.open(image_input) as img:
            return np.array(img.convert("RGB"))
    elif isinstance(image_input, bytes):
        with Image.open(io.BytesIO(image_input)) as img:
            return np.array(img.convert("RGB"))
    else:
        raise ValueError(f"Unsupported image input type: {type(image_input)}")

def ocr_local_easyocr(image_input, lang_key="ur_en", progress_callback=None):
    """
    Run local EasyOCR on the image.
    Preserves line breaks based on bounding box vertical sorting.
    """
    if progress_callback:
        progress_callback("Initializing Local OCR Reader...")
    
    reader = get_easyocr_reader(lang_key)
    img_np = image_to_numpy(image_input)
    
    if progress_callback:
        progress_callback("Scanning text and recognizing characters...")
    
    # Run reader
    results = reader.readtext(img_np, paragraph=True)
    
    if not results:
        # Try without paragraph grouping if nothing was detected
        results = reader.readtext(img_np, paragraph=False)
        if not results:
            return ""
        
        # Sort lines top-to-bottom
        results.sort(key=lambda r: (r[0][0][1], r[0][0][0]))
        lines = [r[1].strip() for r in results if r[1].strip()]
        return "\n".join(lines)
    
    # Results with paragraph=True are typically [[bbox, text], ...]
    lines = []
    for item in results:
        if len(item) >= 2:
            text = item[1].strip()
            if text:
                lines.append(text)
    
    return "\n\n".join(lines)

def ocr_cloud_gemini(image_input, api_key, model="gemini-2.5-flash", lang_hint="Urdu, Arabic, English", progress_callback=None):
    """
    Free Cloud AI OCR using Google Gemini Vision API.
    Provides extraordinary recognition for Nastaliq Urdu script, calligraphy, and handwritten text.
    """
    if not api_key or not api_key.strip():
        raise ValueError("Google Gemini API Key is required for Cloud AI mode. You can get one for free at https://aistudio.google.com")
    
    if progress_callback:
        progress_callback("Preparing image for Cloud AI OCR...")
    
    # Convert image to JPEG bytes
    if isinstance(image_input, Image.Image):
        buffered = io.BytesIO()
        image_input.convert("RGB").save(buffered, format="JPEG", quality=95)
        img_bytes = buffered.getvalue()
    elif isinstance(image_input, str):
        with open(image_input, "rb") as f:
            img_bytes = f.read()
    elif isinstance(image_input, np.ndarray):
        img_pil = Image.fromarray(image_input)
        buffered = io.BytesIO()
        img_pil.convert("RGB").save(buffered, format="JPEG", quality=95)
        img_bytes = buffered.getvalue()
    elif isinstance(image_input, bytes):
        img_bytes = image_input
    else:
        raise ValueError(f"Unsupported image input type: {type(image_input)}")
    
    b64_data = base64.b64encode(img_bytes).decode("utf-8")
    
    if progress_callback:
        progress_callback("Sending request to Gemini Free API...")
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key.strip()}"
    headers = {"Content-Type": "application/json"}
    
    prompt = (
        "You are an expert high-precision OCR transcription engine. "
        "Transcribe ALL visible text from this image exactly as written. "
        f"Accurately recognize languages including {lang_hint} and numbers. "
        "Preserve original line breaks, formatting, and paragraphs. "
        "Do NOT add conversational remarks, introductory words, or markdown quotes. "
        "Output ONLY the exact transcribed text."
    )
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": b64_data
                        }
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 8192
        }
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=45)
    
    if response.status_code != 200:
        err_msg = response.text
        try:
            err_json = response.json()
            if "error" in err_json and "message" in err_json["error"]:
                err_msg = err_json["error"]["message"]
        except Exception:
            pass
        raise RuntimeError(f"Gemini API Error ({response.status_code}): {err_msg}")
    
    data = response.json()
    try:
        candidates = data.get("candidates", [])
        if candidates and "content" in candidates[0]:
            parts = candidates[0]["content"].get("parts", [])
            extracted_text = "".join(p.get("text", "") for p in parts)
            return extracted_text.strip()
        else:
            return ""
    except Exception as e:
        raise RuntimeError(f"Error parsing Gemini response: {e}")

def recognize_text(image_input, engine="local", lang_key="ur_en", api_key="", model="gemini-2.5-flash", progress_callback=None):
    """
    Main dispatch function for OCR.
    """
    if engine == "cloud":
        return ocr_cloud_gemini(
            image_input,
            api_key=api_key,
            model=model,
            lang_hint=LANG_CONFIGS.get(lang_key, {}).get("name", "Urdu, Arabic, English"),
            progress_callback=progress_callback
        )
    else:
        return ocr_local_easyocr(
            image_input,
            lang_key=lang_key,
            progress_callback=progress_callback
        )
