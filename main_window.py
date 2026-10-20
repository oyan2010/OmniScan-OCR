"""
Main Desktop Application Window for OmniScan OCR.
Provides a comprehensive suite for:
- Screen Snip & History
- PDF Text & Page Range OCR
- Image File Upload & Batch Recognition
- Settings & Language Engine configuration
"""
import os
import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QTextEdit, QLineEdit, QComboBox, QCheckBox,
    QFileDialog, QProgressBar, QSplitter, QListWidget, QListWidgetItem,
    QMessageBox, QRadioButton, QButtonGroup, QGroupBox, QFrame, QApplication
)
from PyQt6.QtGui import QFont, QColor, QPixmap, QIcon
from PyQt6.QtCore import Qt, QThread, pyqtSignal

import pyperclip
from config import load_config, save_config
from ocr_engine import recognize_text, LANG_CONFIGS
from pdf_processor import process_pdf, get_pdf_info
from snipping_overlay import SnippingOverlay
from result_dialog import ResultDialog
from floating_bar import FloatingBar

# OCR Worker Thread for Screen & Image OCR to prevent UI freezing
class OCRWorkerThread(QThread):
    finished_signal = pyqtSignal(str, object)  # text, original_image
    error_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(str)
    
    def __init__(self, image_input, engine, lang_key, api_key):
        super().__init__()
        self.image_input = image_input
        self.engine = engine
        self.lang_key = lang_key
        self.api_key = api_key
        
    def run(self):
        try:
            def progress(msg):
                self.progress_signal.emit(msg)
                
            text = recognize_text(
                self.image_input,
                engine=self.engine,
                lang_key=self.lang_key,
                api_key=self.api_key,
                progress_callback=progress
            )
            self.finished_signal.emit(text, self.image_input)
        except Exception as e:
            self.error_signal.emit(str(e))

# PDF Worker Thread
class PDFWorkerThread(QThread):
    progress_signal = pyqtSignal(int, int, int, str)  # current, total, page_num, text
    finished_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)
    
    def __init__(self, pdf_path, page_range, mode, engine, lang_key, api_key, dpi):
        super().__init__()
        self.pdf_path = pdf_path
        self.page_range = page_range
        self.mode = mode
        self.engine = engine
        self.lang_key = lang_key
        self.api_key = api_key
        self.dpi = dpi
        
    def run(self):
        try:
            def progress(cur, tot, p_num, msg):
                self.progress_signal.emit(cur, tot, p_num, msg)
                
            result = process_pdf(
                self.pdf_path,
                page_range_str=self.page_range,
                mode=self.mode,
                engine=self.engine,
                lang_key=self.lang_key,
                api_key=self.api_key,
                dpi=self.dpi,
                progress_callback=progress
            )
            self.finished_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OmniScan OCR Studio - Multi-Language Screen & Doc OCR")
        self.resize(1050, 720)
        
        self.config = load_config()
        self.snipper = SnippingOverlay()
        self.snipper.snip_captured.connect(self.on_snip_captured)
        
        self.floating_bar = FloatingBar(
            current_lang=self.config.get("language", "ur_en"),
            current_engine=self.config.get("engine", "local")
        )
        self.floating_bar.snip_clicked.connect(self.start_snip)
        self.floating_bar.open_main_clicked.connect(self.show_and_activate)
        self.floating_bar.pdf_clicked.connect(self.open_pdf_tab)
        self.floating_bar.image_clicked.connect(self.open_image_tab)
        self.floating_bar.language_changed.connect(self.on_language_changed)
        self.floating_bar.engine_toggled.connect(self.on_engine_toggled)
        
        self.history_items = []
        self.current_loaded_image = None
        self.current_pdf_path = None
        
        self.apply_theme()
        self.init_ui()
        
        if self.config.get("floating_bar_visible", True):
            self.floating_bar.move(100, 80)
            self.floating_bar.show()
            
    def apply_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0d1117;
            }
            QTabWidget::pane {
                border: 1px solid #30363d;
                background-color: #161b22;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #161b22;
                color: #8b949e;
                border: 1px solid #30363d;
                border-bottom: none;
                padding: 10px 22px;
                font-size: 13px;
                font-weight: 600;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background-color: #21262d;
                color: #58a6ff;
                border-bottom: 2px solid #58a6ff;
            }
            QTabBar::tab:hover {
                color: #f0f6fc;
            }
            QGroupBox {
                border: 1px solid #30363d;
                border-radius: 8px;
                margin-top: 12px;
                font-size: 12px;
                font-weight: bold;
                color: #58a6ff;
                padding-top: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
            }
            QPushButton {
                background-color: #21262d;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #30363d;
                color: #58a6ff;
                border-color: #58a6ff;
            }
            QPushButton#primaryActionBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #2563eb);
                color: #ffffff;
                border: 1px solid #38bdf8;
                font-weight: bold;
                font-size: 14px;
                padding: 10px 20px;
                border-radius: 8px;
            }
            QPushButton#primaryActionBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0369a1, stop:1 #1d4ed8);
            }
            QTextEdit, QLineEdit, QListWidget {
                background-color: #0d1117;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 8px;
                font-family: 'Segoe UI', 'Noto Nastaliq Urdu', 'Arial';
                font-size: 14px;
            }
            QComboBox {
                background-color: #21262d;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QProgressBar {
                border: 1px solid #30363d;
                border-radius: 4px;
                text-align: center;
                background-color: #0d1117;
                color: #f0f6fc;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #238636;
                border-radius: 3px;
            }
            QLabel {
                color: #c9d1d9;
            }
        """)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 12, 16, 16)
        main_layout.setSpacing(10)
        
        # Top Global Bar
        top_bar = QHBoxLayout()
        logo_label = QLabel("⚡ OmniScan OCR")
        logo_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #f0f6fc;")
        top_bar.addWidget(logo_label)
        
        top_bar.addSpacing(16)
        
        # Quick status badge
        self.lbl_engine_status = QLabel()
        self.update_engine_status_label()
        top_bar.addWidget(self.lbl_engine_status)
        
        top_bar.addStretch()
        
        # Floating Bar toggle
        self.chk_floating = QCheckBox("Show Floating Screen Bar")
        self.chk_floating.setChecked(self.config.get("floating_bar_visible", True))
        self.chk_floating.toggled.connect(self.toggle_floating_bar)
        top_bar.addWidget(self.chk_floating)
        
        top_bar.addSpacing(10)
        
        # Big Snip button in top bar
        btn_top_snip = QPushButton("✂ Snip Screen Area")
        btn_top_snip.setObjectName("primaryActionBtn")
        btn_top_snip.setToolTip("Hotkey: Ctrl+Alt+S")
        btn_top_snip.clicked.connect(self.start_snip)
        top_bar.addWidget(btn_top_snip)
        
        main_layout.addLayout(top_bar)
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_snip_tab(), "✂ Screen Snip & History")
        self.tabs.addTab(self.create_pdf_tab(), "📄 PDF Document OCR")
        self.tabs.addTab(self.create_image_tab(), "🖼️ Image & Screenshot Files")
        self.tabs.addTab(self.create_settings_tab(), "⚙️ Settings & Languages")
        
        main_layout.addWidget(self.tabs)
        
        # Bottom Status Bar
        self.status_label = QLabel("Ready. Press 'Snip Screen Area' or upload a document to begin.")
        self.status_label.setStyleSheet("color: #8b949e; font-size: 12px; padding-top: 4px;")
        main_layout.addWidget(self.status_label)

    def update_engine_status_label(self):
        engine = self.config.get("engine", "local")
        lang = self.config.get("language", "ur_en")
        lang_name = LANG_CONFIGS.get(lang, {}).get("name", "Urdu + English")
        if engine == "cloud":
            self.lbl_engine_status.setText(f"Mode: ☁ Gemini Cloud AI  •  Language: {lang_name}")
            self.lbl_engine_status.setStyleSheet("color: #a855f7; font-weight: bold;")
        else:
            self.lbl_engine_status.setText(f"Mode: 💻 100% Offline Local  •  Language: {lang_name}")
            self.lbl_engine_status.setStyleSheet("color: #38bdf8; font-weight: bold;")

    # --- TAB 1: Screen Snip & History ---
    def create_snip_tab(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side: History list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 8, 0)
        
        history_header = QHBoxLayout()
        history_title = QLabel("Recent Captures")
        history_title.setStyleSheet("font-weight: bold; color: #58a6ff;")
        history_header.addWidget(history_title)
        history_header.addStretch()
        
        btn_clear_hist = QPushButton("Clear")
        btn_clear_hist.clicked.connect(self.clear_history)
        history_header.addWidget(btn_clear_hist)
        left_layout.addLayout(history_header)
        
        self.list_history = QListWidget()
        self.list_history.itemClicked.connect(self.on_history_selected)
        left_layout.addWidget(self.list_history)
        
        splitter.addWidget(left_widget)
        
        # Right side: Current Result Viewer
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(8, 0, 0, 0)
        
        # Action Toolbar above editor
        tb_layout = QHBoxLayout()
        tb_label = QLabel("Extracted Text")
        tb_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #f0f6fc;")
        tb_layout.addWidget(tb_label)
        
        tb_layout.addStretch()
        
        btn_clean = QPushButton("Format / Clean")
        btn_clean.setToolTip("Format line breaks and whitespace")
        btn_clean.clicked.connect(self.clean_snip_text)
        tb_layout.addWidget(btn_clean)
        
        btn_save = QPushButton("💾 Save .txt")
        btn_save.clicked.connect(self.save_snip_text)
        tb_layout.addWidget(btn_save)
        
        self.btn_copy_snip = QPushButton("📋 Copy All")
        self.btn_copy_snip.setObjectName("primaryActionBtn")
        self.btn_copy_snip.clicked.connect(self.copy_snip_text)
        tb_layout.addWidget(self.btn_copy_snip)
        
        right_layout.addLayout(tb_layout)
        
        self.text_snip_result = QTextEdit()
        self.text_snip_result.setPlaceholderText("Captured text will appear here immediately after snipping...")
        right_layout.addWidget(self.text_snip_result)
        
        splitter.addWidget(right_widget)
        splitter.setSizes([260, 740])
        
        layout.addWidget(splitter)
        return tab

    # --- TAB 2: PDF Document OCR ---
    def create_pdf_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)
        
        # File selector group
        group_file = QGroupBox("Select PDF Document")
        gf_layout = QHBoxLayout(group_file)
        
        self.lbl_pdf_name = QLabel("No PDF selected. Click 'Browse PDF' or drag & drop a PDF file here.")
        self.lbl_pdf_name.setStyleSheet("color: #8b949e;")
        gf_layout.addWidget(self.lbl_pdf_name, stretch=1)
        
        btn_browse_pdf = QPushButton("📁 Browse PDF")
        btn_browse_pdf.clicked.connect(self.browse_pdf)
        gf_layout.addWidget(btn_browse_pdf)
        layout.addWidget(group_file)
        
        # Options row
        group_opts = QGroupBox("Page Range & Extraction Settings")
        go_layout = QHBoxLayout(group_opts)
        
        # Page range radio group
        self.radio_all_pages = QRadioButton("All Pages")
        self.radio_all_pages.setChecked(True)
        go_layout.addWidget(self.radio_all_pages)
        
        self.radio_range_pages = QRadioButton("Custom Range:")
        go_layout.addWidget(self.radio_range_pages)
        
        self.txt_page_range = QLineEdit()
        self.txt_page_range.setPlaceholderText("e.g. 1-5, 8, 11-15")
        self.txt_page_range.setFixedWidth(160)
        go_layout.addWidget(self.txt_page_range)
        
        go_layout.addSpacing(20)
        
        # Mode selector
        go_layout.addWidget(QLabel("Mode:"))
        self.combo_pdf_mode = QComboBox()
        self.combo_pdf_mode.addItem("Smart (Fast digital + Scanned OCR)", "smart")
        self.combo_pdf_mode.addItem("Force Full OCR (All Pages)", "force_ocr")
        go_layout.addWidget(self.combo_pdf_mode)
        
        go_layout.addSpacing(20)
        
        # DPI
        go_layout.addWidget(QLabel("DPI Quality:"))
        self.combo_pdf_dpi = QComboBox()
        self.combo_pdf_dpi.addItem("200 DPI (Balanced)", 200)
        self.combo_pdf_dpi.addItem("300 DPI (High Clarity)", 300)
        self.combo_pdf_dpi.addItem("150 DPI (Fast)", 150)
        go_layout.addWidget(self.combo_pdf_dpi)
        
        go_layout.addStretch()
        
        self.btn_start_pdf = QPushButton("🚀 Extract PDF Text")
        self.btn_start_pdf.setObjectName("primaryActionBtn")
        self.btn_start_pdf.setEnabled(False)
        self.btn_start_pdf.clicked.connect(self.start_pdf_processing)
        go_layout.addWidget(self.btn_start_pdf)
        
        layout.addWidget(group_opts)
        
        # Progress bar
        self.pdf_progress = QProgressBar()
        self.pdf_progress.setValue(0)
        self.pdf_progress.setVisible(False)
        layout.addWidget(self.pdf_progress)
        
        # Results text editor
        res_header = QHBoxLayout()
        res_title = QLabel("Extracted PDF Content")
        res_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #f0f6fc;")
        res_header.addWidget(res_title)
        res_header.addStretch()
        
        btn_copy_pdf = QPushButton("📋 Copy All")
        btn_copy_pdf.clicked.connect(self.copy_pdf_text)
        res_header.addWidget(btn_copy_pdf)
        
        btn_save_pdf = QPushButton("💾 Save .txt / .md")
        btn_save_pdf.clicked.connect(self.save_pdf_text)
        res_header.addWidget(btn_save_pdf)
        
        layout.addLayout(res_header)
        
        self.text_pdf_result = QTextEdit()
        self.text_pdf_result.setPlaceholderText("Extracted text from your PDF will appear here with page separators...")
        layout.addWidget(self.text_pdf_result, stretch=1)
        
        return tab

    # --- TAB 3: Image File OCR ---
    def create_image_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)
        
        # Top toolbar
        img_tb = QHBoxLayout()
        btn_browse_img = QPushButton("🖼️ Browse Image File")
        btn_browse_img.clicked.connect(self.browse_image)
        img_tb.addWidget(btn_browse_img)
        
        btn_paste_img = QPushButton("📋 Paste Image from Clipboard (Ctrl+V)")
        btn_paste_img.clicked.connect(self.paste_image_from_clipboard)
        img_tb.addWidget(btn_paste_img)
        
        img_tb.addStretch()
        
        self.btn_run_img_ocr = QPushButton("⚡ Extract Text From Image")
        self.btn_run_img_ocr.setObjectName("primaryActionBtn")
        self.btn_run_img_ocr.setEnabled(False)
        self.btn_run_img_ocr.clicked.connect(self.run_image_ocr)
        img_tb.addWidget(self.btn_run_img_ocr)
        
        layout.addLayout(img_tb)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Image preview
        self.lbl_image_preview = QLabel("No image loaded.\nClick Browse Image or Paste (Ctrl+V).")
        self.lbl_image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_image_preview.setStyleSheet("""
            background-color: #0d1117;
            border: 2px dashed #30363d;
            border-radius: 8px;
            color: #8b949e;
            font-size: 13px;
        """)
        splitter.addWidget(self.lbl_image_preview)
        
        # Right: Extracted Text
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(8, 0, 0, 0)
        
        img_res_tb = QHBoxLayout()
        img_res_title = QLabel("Extracted Image Text")
        img_res_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #f0f6fc;")
        img_res_tb.addWidget(img_res_title)
        img_res_tb.addStretch()
        
        btn_copy_img = QPushButton("📋 Copy")
        btn_copy_img.clicked.connect(self.copy_image_text)
        img_res_tb.addWidget(btn_copy_img)
        
        btn_save_img = QPushButton("💾 Save .txt")
        btn_save_img.clicked.connect(self.save_image_text)
        img_res_tb.addWidget(btn_save_img)
        
        right_layout.addLayout(img_res_tb)
        
        self.text_image_result = QTextEdit()
        self.text_image_result.setPlaceholderText("Text extracted from the loaded image will appear here...")
        right_layout.addWidget(self.text_image_result)
        
        splitter.addWidget(right_widget)
        splitter.setSizes([380, 620])
        
        layout.addWidget(splitter, stretch=1)
        return tab

    # --- TAB 4: Settings & Configuration ---
    def create_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)
        
        # Engine group
        grp_engine = QGroupBox("OCR Engine Selection")
        ge_layout = QVBoxLayout(grp_engine)
        
        self.radio_local_engine = QRadioButton("Local Engine (100% Offline, Private, Zero Internet Required)")
        self.radio_cloud_engine = QRadioButton("Free Cloud AI Engine (Google Gemini Vision - Exceptional for Nastaliq Urdu)")
        
        if self.config.get("engine", "local") == "cloud":
            self.radio_cloud_engine.setChecked(True)
        else:
            self.radio_local_engine.setChecked(True)
            
        self.radio_local_engine.toggled.connect(self.on_engine_radio_changed)
        ge_layout.addWidget(self.radio_local_engine)
        ge_layout.addWidget(self.radio_cloud_engine)
        
        layout.addWidget(grp_engine)
        
        # Cloud API Key group
        grp_cloud = QGroupBox("Google Gemini Free API Key (Required ONLY for Cloud AI Mode)")
        gc_layout = QVBoxLayout(grp_cloud)
        
        key_row = QHBoxLayout()
        key_row.addWidget(QLabel("API Key:"))
        self.txt_gemini_key = QLineEdit()
        self.txt_gemini_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_gemini_key.setText(self.config.get("gemini_api_key", ""))
        self.txt_gemini_key.setPlaceholderText("Paste your free Google AI Studio API key here...")
        key_row.addWidget(self.txt_gemini_key, stretch=1)
        
        btn_show_key = QPushButton("👁")
        btn_show_key.setFixedWidth(36)
        btn_show_key.clicked.connect(self.toggle_key_visibility)
        key_row.addWidget(btn_show_key)
        gc_layout.addLayout(key_row)
        
        lbl_hint = QLabel("💡 Tip: You can get a free, unlimited-use API key from https://aistudio.google.com with zero credit card required.")
        lbl_hint.setStyleSheet("color: #8b949e; font-size: 11px;")
        lbl_hint.setOpenExternalLinks(True)
        gc_layout.addWidget(lbl_hint)
        
        layout.addWidget(grp_cloud)
        
        # Language & Behavior
        grp_behavior = QGroupBox("Language & Preferences")
        gb_layout = QVBoxLayout(grp_behavior)
        
        lang_row = QHBoxLayout()
        lang_row.addWidget(QLabel("Default Language:"))
        self.combo_default_lang = QComboBox()
        self.combo_default_lang.addItem("Urdu + English", "ur_en")
        self.combo_default_lang.addItem("Arabic + English", "ar_en")
        self.combo_default_lang.addItem("English Only", "en")
        self.combo_default_lang.addItem("Persian + English", "fa_en")
        self.combo_default_lang.addItem("Hindi + English", "hi_en")
        
        idx = self.combo_default_lang.findData(self.config.get("language", "ur_en"))
        if idx >= 0:
            self.combo_default_lang.setCurrentIndex(idx)
        lang_row.addWidget(self.combo_default_lang)
        lang_row.addStretch()
        gb_layout.addLayout(lang_row)
        
        self.chk_auto_copy = QCheckBox("Automatically copy extracted text to clipboard")
        self.chk_auto_copy.setChecked(self.config.get("auto_copy_clipboard", True))
        gb_layout.addWidget(self.chk_auto_copy)
        
        layout.addWidget(grp_behavior)
        
        # Save Settings button
        btn_save_settings = QPushButton("💾 Save Preferences")
        btn_save_settings.setObjectName("primaryActionBtn")
        btn_save_settings.clicked.connect(self.save_settings)
        layout.addWidget(btn_save_settings)
        
        layout.addStretch()
        return tab

    # --- Handlers & Actions ---
    def start_snip(self):
        """Minimize or hide windows if needed and launch snipper."""
        self.snipper.start_snip()
        
    def on_snip_captured(self, pil_image):
        self.status_label.setText("Extracting text from snip...")
        engine = self.config.get("engine", "local")
        lang = self.config.get("language", "ur_en")
        api_key = self.config.get("gemini_api_key", "")
        
        # Start worker thread
        self.worker = OCRWorkerThread(pil_image, engine, lang, api_key)
        self.worker.progress_signal.connect(lambda msg: self.status_label.setText(msg))
        self.worker.finished_signal.connect(self.on_snip_ocr_finished)
        self.worker.error_signal.connect(self.on_ocr_error)
        self.worker.start()
        
    def on_snip_ocr_finished(self, text, original_img):
        self.status_label.setText("Text extracted successfully!")
        
        # Auto-copy to clipboard if enabled
        if self.config.get("auto_copy_clipboard", True):
            try:
                pyperclip.copy(text)
            except Exception:
                QApplication.clipboard().setText(text)
                
        # Set text in main window editor
        self.text_snip_result.setPlainText(text)
        
        # Add to history
        preview = text.strip().split("\n")[0][:40] if text.strip() else "(No text)"
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        hist_label = f"[{timestamp}] {preview}"
        item = QListWidgetItem(hist_label)
        self.list_history.insertItem(0, item)
        self.history_items.insert(0, {"text": text, "image": original_img})
        
        # Determine RTL
        lang = self.config.get("language", "ur_en")
        is_rtl = LANG_CONFIGS.get(lang, {}).get("is_rtl", False)
        
        # Show floating quick result dialog
        engine_name = "Cloud AI" if self.config.get("engine") == "cloud" else "Local EasyOCR"
        dlg = ResultDialog(self, text=text, image=original_img, engine_info=engine_name, is_rtl=is_rtl)
        dlg.show()
        
    def on_ocr_error(self, err_msg):
        self.status_label.setText("Error during OCR extraction.")
        QMessageBox.critical(self, "OCR Error", f"Failed to extract text:\n\n{err_msg}")
        
    def on_history_selected(self, item):
        row = self.list_history.row(item)
        if 0 <= row < len(self.history_items):
            self.text_snip_result.setPlainText(self.history_items[row]["text"])
            
    def clear_history(self):
        self.list_history.clear()
        self.history_items.clear()
        
    def copy_snip_text(self):
        text = self.text_snip_result.toPlainText()
        try:
            pyperclip.copy(text)
        except Exception:
            QApplication.clipboard().setText(text)
        self.btn_copy_snip.setText("✓ Copied!")
        self.status_label.setText("Copied to clipboard.")
        
    def clean_snip_text(self):
        raw = self.text_snip_result.toPlainText()
        paragraphs = raw.split("\n\n")
        cleaned = [" ".join(line.strip() for line in p.split("\n") if line.strip()) for p in paragraphs]
        self.text_snip_result.setPlainText("\n\n".join(c for c in cleaned if c))
        
    def save_snip_text(self):
        text = self.text_snip_result.toPlainText()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Text", "extracted_snip.txt", "Text Files (*.txt);;All Files (*)")
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text)
            self.status_label.setText(f"Saved to {file_path}")

    # --- PDF Tab Handlers ---
    def browse_pdf(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select PDF Document", "", "PDF Files (*.pdf)")
        if path:
            self.load_pdf_file(path)
            
    def load_pdf_file(self, path):
        self.current_pdf_path = path
        try:
            info = get_pdf_info(path)
            filename = os.path.basename(path)
            self.lbl_pdf_name.setText(f"📄 {filename}  •  {info['total_pages']} pages")
            self.btn_start_pdf.setEnabled(True)
            self.status_label.setText(f"PDF loaded: {filename} ({info['total_pages']} pages)")
        except Exception as e:
            QMessageBox.warning(self, "PDF Load Error", str(e))
            
    def start_pdf_processing(self):
        if not self.current_pdf_path:
            return
            
        page_range = "all"
        if self.radio_range_pages.isChecked():
            page_range = self.txt_page_range.text().strip()
            if not page_range:
                QMessageBox.warning(self, "Page Range Needed", "Please enter a valid page range (e.g. 1-5, 8).")
                return
                
        mode = self.combo_pdf_mode.currentData()
        dpi = self.combo_pdf_dpi.currentData()
        engine = self.config.get("engine", "local")
        lang = self.config.get("language", "ur_en")
        api_key = self.config.get("gemini_api_key", "")
        
        self.btn_start_pdf.setEnabled(False)
        self.pdf_progress.setValue(0)
        self.pdf_progress.setVisible(True)
        self.text_pdf_result.clear()
        
        self.pdf_worker = PDFWorkerThread(
            self.current_pdf_path,
            page_range=page_range,
            mode=mode,
            engine=engine,
            lang_key=lang,
            api_key=api_key,
            dpi=dpi
        )
        self.pdf_worker.progress_signal.connect(self.on_pdf_progress)
        self.pdf_worker.finished_signal.connect(self.on_pdf_finished)
        self.pdf_worker.error_signal.connect(self.on_pdf_error)
        self.pdf_worker.start()
        
    def on_pdf_progress(self, current, total, page_num, text_or_msg):
        pct = int((current / max(1, total)) * 100)
        self.pdf_progress.setValue(pct)
        self.status_label.setText(f"Processing PDF page {page_num} ({current}/{total})...")
        
    def on_pdf_finished(self, result):
        self.btn_start_pdf.setEnabled(True)
        self.pdf_progress.setVisible(False)
        self.text_pdf_result.setPlainText(result["full_text"])
        self.status_label.setText(f"PDF extraction complete! ({result['total_processed']} pages processed)")
        
        if self.config.get("auto_copy_clipboard", True):
            try:
                pyperclip.copy(result["full_text"])
            except Exception:
                pass
                
    def on_pdf_error(self, err_msg):
        self.btn_start_pdf.setEnabled(True)
        self.pdf_progress.setVisible(False)
        self.status_label.setText("Error during PDF processing.")
        QMessageBox.critical(self, "PDF Error", f"Failed to process PDF:\n\n{err_msg}")
        
    def copy_pdf_text(self):
        text = self.text_pdf_result.toPlainText()
        try:
            pyperclip.copy(text)
        except Exception:
            QApplication.clipboard().setText(text)
        self.status_label.setText("PDF text copied to clipboard.")
        
    def save_pdf_text(self):
        text = self.text_pdf_result.toPlainText()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save PDF Extracted Text", "extracted_document.txt", "Text Files (*.txt);;Markdown (*.md)")
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text)
            self.status_label.setText(f"Saved to {file_path}")

    # --- Image Tab Handlers ---
    def browse_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.webp *.tiff)")
        if path:
            self.load_image_file(path)
            
    def load_image_file(self, path):
        from PIL import Image
        try:
            pil_img = Image.open(path)
            self.current_loaded_image = pil_img
            pix = QPixmap(path)
            scaled = pix.scaled(350, 350, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.lbl_image_preview.setPixmap(scaled)
            self.btn_run_img_ocr.setEnabled(True)
            self.status_label.setText(f"Loaded image: {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.warning(self, "Image Error", str(e))
            
    def paste_image_from_clipboard(self):
        clipboard = QApplication.clipboard()
        qimg = clipboard.image()
        if not qimg.isNull():
            from PIL import Image
            from PyQt6.QtCore import QBuffer, QIODevice
            qbuffer = QBuffer()
            qbuffer.open(QIODevice.OpenModeFlag.ReadWrite)
            qimg.save(qbuffer, "PNG")
            bytes_data = bytes(qbuffer.data())
            qbuffer.close()
            
            import io
            pil_img = Image.open(io.BytesIO(bytes_data))
            self.current_loaded_image = pil_img
            
            pix = QPixmap.fromImage(qimg)
            scaled = pix.scaled(350, 350, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.lbl_image_preview.setPixmap(scaled)
            self.btn_run_img_ocr.setEnabled(True)
            self.status_label.setText("Pasted image from clipboard.")
        else:
            QMessageBox.information(self, "Clipboard", "No image found in clipboard. Press PrintScreen or copy an image first.")
            
    def run_image_ocr(self):
        if not self.current_loaded_image:
            return
            
        self.btn_run_img_ocr.setEnabled(False)
        self.status_label.setText("Running OCR on image...")
        
        engine = self.config.get("engine", "local")
        lang = self.config.get("language", "ur_en")
        api_key = self.config.get("gemini_api_key", "")
        
        self.img_worker = OCRWorkerThread(self.current_loaded_image, engine, lang, api_key)
        self.img_worker.progress_signal.connect(lambda msg: self.status_label.setText(msg))
        self.img_worker.finished_signal.connect(self.on_image_ocr_finished)
        self.img_worker.error_signal.connect(self.on_image_ocr_error)
        self.img_worker.start()
        
    def on_image_ocr_finished(self, text, _):
        self.btn_run_img_ocr.setEnabled(True)
        self.text_image_result.setPlainText(text)
        self.status_label.setText("Image OCR completed!")
        if self.config.get("auto_copy_clipboard", True):
            try:
                pyperclip.copy(text)
            except Exception:
                pass
                
    def on_image_ocr_error(self, err_msg):
        self.btn_run_img_ocr.setEnabled(True)
        self.status_label.setText("Error during Image OCR.")
        QMessageBox.critical(self, "OCR Error", str(err_msg))
        
    def copy_image_text(self):
        text = self.text_image_result.toPlainText()
        try:
            pyperclip.copy(text)
        except Exception:
            QApplication.clipboard().setText(text)
        self.status_label.setText("Copied to clipboard.")
        
    def save_image_text(self):
        text = self.text_image_result.toPlainText()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Image Extracted Text", "image_ocr_result.txt", "Text Files (*.txt);;Markdown (*.md)")
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text)
            self.status_label.setText(f"Saved to {file_path}")

    # --- Settings Tab Handlers ---
    def toggle_key_visibility(self):
        if self.txt_gemini_key.echoMode() == QLineEdit.EchoMode.Password:
            self.txt_gemini_key.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.txt_gemini_key.setEchoMode(QLineEdit.EchoMode.Password)
            
    def on_engine_radio_changed(self):
        if self.radio_cloud_engine.isChecked():
            self.config["engine"] = "cloud"
        else:
            self.config["engine"] = "local"
        self.floating_bar.set_engine(self.config["engine"])
        self.update_engine_status_label()
        
    def save_settings(self):
        self.config["gemini_api_key"] = self.txt_gemini_key.text().strip()
        self.config["language"] = self.combo_default_lang.currentData()
        self.config["auto_copy_clipboard"] = self.chk_auto_copy.isChecked()
        self.config["engine"] = "cloud" if self.radio_cloud_engine.isChecked() else "local"
        
        save_config(self.config)
        self.floating_bar.set_language(self.config["language"])
        self.floating_bar.set_engine(self.config["engine"])
        self.update_engine_status_label()
        QMessageBox.information(self, "Settings", "Preferences saved successfully!")

    # --- Floating Bar & App Switchers ---
    def toggle_floating_bar(self, checked):
        self.config["floating_bar_visible"] = checked
        save_config(self.config)
        if checked:
            self.floating_bar.show()
        else:
            self.floating_bar.hide()
            
    def on_language_changed(self, lang_key):
        self.config["language"] = lang_key
        save_config(self.config)
        idx = self.combo_default_lang.findData(lang_key)
        if idx >= 0:
            self.combo_default_lang.setCurrentIndex(idx)
        self.update_engine_status_label()
        
    def on_engine_toggled(self, engine_name):
        self.config["engine"] = engine_name
        save_config(self.config)
        if engine_name == "cloud":
            self.radio_cloud_engine.setChecked(True)
        else:
            self.radio_local_engine.setChecked(True)
        self.update_engine_status_label()
        
    def show_and_activate(self):
        self.show()
        self.raise_()
        self.activateWindow()
        
    def open_pdf_tab(self):
        self.show_and_activate()
        self.tabs.setCurrentIndex(1)
        self.browse_pdf()
        
    def open_image_tab(self):
        self.show_and_activate()
        self.tabs.setCurrentIndex(2)
        self.browse_image()

    def closeEvent(self, event):
        """Clean shutdown when user closes the main window."""
        if hasattr(self, 'floating_bar') and self.floating_bar:
            self.floating_bar.close()
        if hasattr(self, 'snipper') and self.snipper:
            self.snipper.close()
        if hasattr(self, 'hotkey_thread') and self.hotkey_thread:
            self.hotkey_thread.stop()
        event.accept()
        QApplication.quit()
