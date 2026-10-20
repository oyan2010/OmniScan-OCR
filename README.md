# OmniScan OCR Studio ⚡
### Universal Screen Snipping, PDF, and Document OCR (Urdu, Arabic, English & Multi-Language)

**OmniScan OCR** is a desktop OCR application that runs on your screen. It allows you to:
1. **Snip Any Screen Section**: Click or press `Ctrl + Alt + S` to drag a selection box over any webpage, video, desktop app, or document to extract text and copy it to your clipboard.
2. **Floating On-Screen Toolbar**: A draggable floating pill toolbar that stays on top of all windows for 1-click snipping.
3. **PDF Document Text & Scanned OCR**: Upload any PDF and extract text with custom page ranges (e.g., `1-5`, `3, 7-10`, or `all`).
4. **Image & Screenshot Files**: Upload images or paste from clipboard (`Ctrl + V`) to convert them to text.
5. **Urdu, Arabic, English & More**: Offline models for Urdu Nastaliq/Naskh, Arabic, English, Persian, and Hindi, with native Right-to-Left (RTL) formatting.
6. **100% Offline Local or Free Cloud AI**:
   - **Local Mode (Default)**: 100% offline, private, zero internet required (powered by EasyOCR & PyMuPDF).
   - **Free Cloud AI Mode (Optional)**: Powered by Google Gemini Flash (free tier) for complex Nastaliq handwritten calligraphy and book scans.

---

## 🚀 Quick Start

### 1. Launch with One Click
Double-click `start_omniscan.bat` or run:
```bash
python run.py
```

---

## 🌟 Key Features

### ✂ 1. Screen Snipping Tool
- **Hotkey**: Press `Ctrl + Alt + S` anywhere in Windows (even when minimized).
- **Floating Bar**: Click **✂ Snip Screen** on the floating widget on your screen.
- Drag a rectangle over any part of your screen.
- **Instant Result**:
  - Automatically copies extracted text to clipboard.
  - Displays a floating result card with one-click **Copy**, **Clean / Format**, and **Save as .txt**.
  - Automatically detects Urdu / Arabic and applies Right-to-Left (RTL) reading view.

### 📄 2. PDF Document Extractor & OCR
- **Fast Smart Extraction**: If the PDF has digital text, extracts it in milliseconds!
- **Scanned Page OCR**: If the PDF is scanned images, renders pages at high resolution (150-300 DPI) and performs OCR.
- **Custom Page Ranges**:
  - All pages
  - Ranges like `1-10`
  - Specific pages like `1, 3, 5-8, 12`
- **Progress Tracking**: Real-time progress bar for each page.
- **Export**: Export full document text to `.txt` or `.md`.

### 🖼️ 3. Image & Screenshot File OCR
- Drag and drop image files (`.png`, `.jpg`, `.jpeg`, `.bmp`, `.webp`, `.tiff`).
- Paste screenshots directly from clipboard using `Ctrl + V`.
- Live image preview before text extraction.

### 🌐 4. Multi-Language Support
- **Urdu + English** (`ur_en`)
- **Arabic + English** (`ar_en`)
- **English Only** (`en`)
- **Persian (Farsi) + English** (`fa_en`)
- **Hindi + English** (`hi_en`)

### 💻 5. Dual Engine: Local Offline & Free Cloud
- **Local Engine (Default)**:
  - Runs completely on your PC with pre-downloaded offline neural weights.
  - Zero cloud calls, 100% private.
- **Free Cloud AI Engine (Optional)**:
  - Uses Google Gemini 2.5 Flash free tier (15 requests/minute, free forever).
  - Unmatched accuracy for complex Urdu Nastaliq calligraphy, faded scans, and handwriting.
  - Simply paste your free API key in the **Settings** tab (from [Google AI Studio](https://aistudio.google.com)).

---

## 📁 Project Structure

```
f:\Python\Projects\OVTX\
├── config.py             # User settings & preferences persistence
├── ocr_engine.py         # Unified EasyOCR + Gemini Cloud AI Engine
├── snipping_overlay.py   # Fullscreen crosshair selection overlay
├── floating_bar.py       # Draggable on-screen floating pill toolbar
├── result_dialog.py      # Quick floating result popup with RTL & copy actions
├── pdf_processor.py      # PyMuPDF fast text extractor with page ranges
├── main_window.py        # Comprehensive PyQt6 desktop studio
├── hotkey_listener.py    # Native Win32 global hotkey thread (Ctrl+Alt+S)
├── run.py                # Application entry point with System Tray
├── test_suite.py         # Automated verification tests
└── start_omniscan.bat    # Windows 1-click launcher
```

---

## ⌨️ Shortcuts Reference
- `Ctrl + Alt + S`: Activate screen snip overlay from any application.
- `Esc` or `Right-Click`: Cancel screen snip without capturing.
- `Ctrl + V`: Paste image from clipboard in the Image OCR tab.
