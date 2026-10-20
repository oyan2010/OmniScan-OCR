"""
Quick OCR Result Dialog for OmniScan OCR.
Displays recognized text with automatic RTL/LTR detection, one-click copy, and file export.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, 
    QLabel, QFrame, QFileDialog, QApplication, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QFont, QColor, QPixmap, QImage, QPainter
from PyQt6.QtCore import Qt, QBuffer, QIODevice
import pyperclip
import os

class ResultDialog(QDialog):
    """Modern floating result popup displaying extracted text."""
    
    def __init__(self, parent=None, text="", image=None, engine_info="", is_rtl=False):
        super().__init__(parent)
        self.setWindowTitle("OCR Extraction Result")
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        self.resize(600, 420)
        self.setStyleSheet("""
            QDialog {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 12px;
            }
            QTextEdit {
                background-color: #0d1117;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 12px;
                font-family: 'Segoe UI', 'Noto Nastaliq Urdu', 'Arial';
                font-size: 15px;
                line-height: 1.5;
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
            QPushButton#primaryBtn {
                background-color: #238636;
                color: #ffffff;
                border: 1px solid #2ea043;
                font-weight: bold;
            }
            QPushButton#primaryBtn:hover {
                background-color: #2ea043;
            }
            QLabel {
                color: #8b949e;
                font-size: 12px;
            }
        """)
        
        self.text_content = text
        self.pil_image = image
        self.init_ui(engine_info, is_rtl)
        
    def init_ui(self, engine_info, is_rtl):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        
        # Header bar
        header_layout = QHBoxLayout()
        title_label = QLabel("✨ Text Extracted Successfully")
        title_label.setStyleSheet("color: #f0f6fc; font-size: 15px; font-weight: bold;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Engine badge
        engine_badge = QLabel(f"  {engine_info or 'Local Engine'}  ")
        engine_badge.setStyleSheet("""
            background-color: #1f2937;
            color: #38bdf8;
            border: 1px solid #0284c7;
            border-radius: 10px;
            padding: 2px 8px;
            font-size: 11px;
            font-weight: bold;
        """)
        header_layout.addWidget(engine_badge)
        
        layout.addLayout(header_layout)
        
        # Middle row: Thumbnail preview (if available) + Text Box
        content_layout = QHBoxLayout()
        
        if self.pil_image:
            # Show small thumbnail of captured image
            thumb_label = QLabel()
            thumb_label.setFixedSize(110, 110)
            thumb_label.setStyleSheet("""
                background-color: #0d1117;
                border: 1px solid #30363d;
                border-radius: 6px;
            """)
            thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            try:
                # Convert PIL to QPixmap
                from PIL.ImageQt import ImageQt
                qimg = ImageQt(self.pil_image)
                pixmap = QPixmap.fromImage(qimg)
                scaled_pixmap = pixmap.scaled(
                    100, 100, 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
                thumb_label.setPixmap(scaled_pixmap)
                content_layout.addWidget(thumb_label)
            except Exception:
                pass
                
        # Text Editor
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(self.text_content)
        
        # Apply RTL direction if Urdu or Arabic
        if is_rtl:
            self.text_edit.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            self.text_edit.setFont(QFont("Noto Nastaliq Urdu, Jameel Noori Nastaleeq, Segoe UI", 15))
        else:
            self.text_edit.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
            self.text_edit.setFont(QFont("Segoe UI", 13))
            
        content_layout.addWidget(self.text_edit, stretch=1)
        layout.addLayout(content_layout, stretch=1)
        
        # Bottom Action Bar
        bottom_layout = QHBoxLayout()
        
        # Character count
        char_count = len(self.text_content)
        words_count = len(self.text_content.split())
        self.info_label = QLabel(f"{words_count} words  •  {char_count} characters")
        bottom_layout.addWidget(self.info_label)
        
        bottom_layout.addStretch()
        
        # Clean Text button
        btn_clean = QPushButton("Format / Clean")
        btn_clean.setToolTip("Remove accidental linebreaks and trim whitespace")
        btn_clean.clicked.connect(self.clean_text)
        bottom_layout.addWidget(btn_clean)
        
        # Save as TXT
        btn_save = QPushButton("💾 Save .txt")
        btn_save.clicked.connect(self.save_text_file)
        bottom_layout.addWidget(btn_save)
        
        # Copy to Clipboard
        self.btn_copy = QPushButton("📋 Copy to Clipboard")
        self.btn_copy.setObjectName("primaryBtn")
        self.btn_copy.clicked.connect(self.copy_to_clipboard)
        bottom_layout.addWidget(self.btn_copy)
        
        layout.addLayout(bottom_layout)
        
    def copy_to_clipboard(self):
        text = self.text_edit.toPlainText()
        try:
            pyperclip.copy(text)
        except Exception:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            
        self.btn_copy.setText("✓ Copied!")
        self.btn_copy.setStyleSheet("background-color: #1f6feb; border-color: #388bfd;")
        
    def clean_text(self):
        """Format text by removing awkward line splits while preserving paragraphs."""
        raw = self.text_edit.toPlainText()
        paragraphs = raw.split("\n\n")
        cleaned_paras = []
        for p in paragraphs:
            # Replace single newlines with spaces inside each paragraph
            cleaned = " ".join(line.strip() for line in p.split("\n") if line.strip())
            if cleaned:
                cleaned_paras.append(cleaned)
        cleaned_text = "\n\n".join(cleaned_paras)
        self.text_edit.setPlainText(cleaned_text)
        
    def save_text_file(self):
        text = self.text_edit.toPlainText()
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Extracted Text", 
            os.path.expanduser("~/Documents/extracted_text.txt"), 
            "Text Files (*.txt);;Markdown Files (*.md);;All Files (*)"
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text)
            self.info_label.setText(f"✓ Saved to {os.path.basename(file_path)}")
