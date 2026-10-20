"""
Always-On Floating Pill Toolbar for OmniScan OCR.
Stays on top of all windows and applications on screen for instant 1-click screen snipping.
"""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QComboBox, 
    QLabel, QGraphicsDropShadowEffect, QMenu
)
from PyQt6.QtGui import QColor, QFont, QCursor, QAction
from PyQt6.QtCore import Qt, QPoint, pyqtSignal

class FloatingBar(QWidget):
    """Sleek floating pill bar docked on screen."""
    
    snip_clicked = pyqtSignal()
    open_main_clicked = pyqtSignal()
    pdf_clicked = pyqtSignal()
    image_clicked = pyqtSignal()
    language_changed = pyqtSignal(str)
    engine_toggled = pyqtSignal(str)
    
    def __init__(self, current_lang="ur_en", current_engine="local"):
        super().__init__()
        self.drag_position = QPoint()
        self.current_lang = current_lang
        self.current_engine = current_engine
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        self.init_ui()
        
    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Pill container
        self.pill = QWidget(self)
        self.pill.setStyleSheet("""
            QWidget {
                background-color: #1e222d;
                border: 1px solid #383f52;
                border-radius: 20px;
            }
            QPushButton {
                background-color: #2b3142;
                color: #e2e8f0;
                border: 1px solid #383f52;
                border-radius: 14px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #3b4259;
                color: #38bdf8;
                border-color: #38bdf8;
            }
            QPushButton#snipBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #2563eb);
                color: #ffffff;
                border: none;
                padding: 6px 14px;
                font-weight: bold;
            }
            QPushButton#snipBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0369a1, stop:1 #1d4ed8);
            }
            QComboBox {
                background-color: #2b3142;
                color: #e2e8f0;
                border: 1px solid #383f52;
                border-radius: 12px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 500;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #1e222d;
                color: #e2e8f0;
                selection-background-color: #2563eb;
                border: 1px solid #383f52;
            }
            QLabel {
                color: #94a3b8;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        
        # Drop shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 5)
        self.pill.setGraphicsEffect(shadow)
        
        pill_layout = QHBoxLayout(self.pill)
        pill_layout.setContentsMargins(12, 6, 12, 6)
        pill_layout.setSpacing(8)
        
        # Drag handle / App Title
        drag_handle = QLabel("⣿ OmniScan")
        drag_handle.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
        drag_handle.setToolTip("Click and drag to move toolbar anywhere on screen")
        pill_layout.addWidget(drag_handle)
        
        # 1. Big Snip Button
        self.btn_snip = QPushButton("✂ Snip Screen")
        self.btn_snip.setObjectName("snipBtn")
        self.btn_snip.setToolTip("Snip any area on screen to capture text (Ctrl+Alt+S)")
        self.btn_snip.clicked.connect(self.snip_clicked.emit)
        pill_layout.addWidget(self.btn_snip)
        
        # 2. PDF Button
        self.btn_pdf = QPushButton("📄 PDF")
        self.btn_pdf.setToolTip("Upload PDF and extract text with custom page ranges")
        self.btn_pdf.clicked.connect(self.pdf_clicked.emit)
        pill_layout.addWidget(self.btn_pdf)
        
        # 3. Image Button
        self.btn_image = QPushButton("🖼️ Image")
        self.btn_image.setToolTip("Upload or paste screenshot image")
        self.btn_image.clicked.connect(self.image_clicked.emit)
        pill_layout.addWidget(self.btn_image)
        
        # 4. Language Selector
        self.combo_lang = QComboBox()
        self.combo_lang.addItem("Urdu + English", "ur_en")
        self.combo_lang.addItem("Arabic + English", "ar_en")
        self.combo_lang.addItem("English Only", "en")
        self.combo_lang.addItem("Persian + English", "fa_en")
        self.combo_lang.addItem("Hindi + English", "hi_en")
        
        idx = self.combo_lang.findData(self.current_lang)
        if idx >= 0:
            self.combo_lang.setCurrentIndex(idx)
        self.combo_lang.currentIndexChanged.connect(self.on_lang_changed)
        pill_layout.addWidget(self.combo_lang)
        
        # 5. Engine Button (Local / Cloud)
        self.btn_engine = QPushButton("💻 Local")
        self.btn_engine.setToolTip("Click to toggle between 100% Offline Local Engine and Free Cloud AI")
        self.update_engine_button()
        self.btn_engine.clicked.connect(self.toggle_engine)
        pill_layout.addWidget(self.btn_engine)
        
        # 6. Studio / Expand button
        self.btn_studio = QPushButton("⛶ Studio")
        self.btn_studio.setToolTip("Open Full OCR Studio Window")
        self.btn_studio.clicked.connect(self.open_main_clicked.emit)
        pill_layout.addWidget(self.btn_studio)
        
        # 7. Close / Hide
        btn_close = QPushButton("✕")
        btn_close.setFixedWidth(26)
        btn_close.setToolTip("Hide floating toolbar (can be reopened from main window or tray)")
        btn_close.clicked.connect(self.hide)
        pill_layout.addWidget(btn_close)
        
        main_layout.addWidget(self.pill)
        self.resize(580, 64)
        
    def update_engine_button(self):
        if self.current_engine == "cloud":
            self.btn_engine.setText("☁ Cloud AI")
            self.btn_engine.setStyleSheet("color: #a855f7; border-color: #a855f7;")
        else:
            self.btn_engine.setText("💻 Local")
            self.btn_engine.setStyleSheet("color: #38bdf8; border-color: #0284c7;")
            
    def toggle_engine(self):
        if self.current_engine == "local":
            self.current_engine = "cloud"
        else:
            self.current_engine = "local"
        self.update_engine_button()
        self.engine_toggled.emit(self.current_engine)
        
    def on_lang_changed(self, index):
        lang_key = self.combo_lang.currentData()
        self.current_lang = lang_key
        self.language_changed.emit(lang_key)
        
    def set_language(self, lang_key):
        idx = self.combo_lang.findData(lang_key)
        if idx >= 0:
            self.combo_lang.setCurrentIndex(idx)
            
    def set_engine(self, engine_name):
        self.current_engine = engine_name
        self.update_engine_button()
        
    # Drag window handling
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
