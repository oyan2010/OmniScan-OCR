"""
Snipping Tool overlay for OmniScan OCR.
Allows dragging a rectangle over any part of the screen to capture and extract text.
Supports multi-monitor, high-DPI scaling (125%, 150%, 200%), and smooth crosshair cursor.
"""
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QCursor
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal
from PIL import Image
import io

class SnippingOverlay(QWidget):
    """Fullscreen translucent overlay for selecting a screen rectangle."""
    snip_captured = pyqtSignal(object)  # Emits PIL.Image
    snip_cancelled = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setCursor(Qt.CursorShape.CrossCursor)
        
        self.start_pos = None
        self.current_pos = None
        self.is_selecting = False
        self.screen_pixmap = None
        self.screen_dpr = 1.0
        
    def start_snip(self):
        """Take screenshot of all screens and open overlay."""
        screen = QApplication.primaryScreen()
        if not screen:
            return
            
        self.screen_dpr = screen.devicePixelRatio()
        virtual_geo = screen.virtualGeometry()
        self.setGeometry(virtual_geo)
        
        # Grab whole screen at native physical resolution
        self.screen_pixmap = screen.grabWindow(0)
        
        self.start_pos = None
        self.current_pos = None
        self.is_selecting = False
        self.showFullScreen()
        self.raise_()
        self.activateWindow()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = event.pos()
            self.current_pos = event.pos()
            self.is_selecting = True
            self.update()
        elif event.button() == Qt.MouseButton.RightButton:
            self.cancel_snip()
            
    def mouseMoveEvent(self, event):
        if self.is_selecting:
            self.current_pos = event.pos()
            self.update()
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_selecting:
            self.is_selecting = False
            self.current_pos = event.pos()
            self.finish_snip()
            
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.cancel_snip()
        else:
            super().keyPressEvent(event)
            
    def cancel_snip(self):
        self.close()
        self.snip_cancelled.emit()
        
    def get_selection_rect(self):
        if not self.start_pos or not self.current_pos:
            return QRect()
        return QRect(self.start_pos, self.current_pos).normalized()
        
    def finish_snip(self):
        rect = self.get_selection_rect()
        self.close()
        
        # Minimum size check to prevent accidental clicks
        if rect.width() < 10 or rect.height() < 10:
            self.snip_cancelled.emit()
            return
            
        if self.screen_pixmap:
            dpr = self.screen_dpr
            # Convert logical coordinates to physical pixels for crisp OCR
            physical_rect = QRect(
                int(round(rect.x() * dpr)),
                int(round(rect.y() * dpr)),
                int(round(rect.width() * dpr)),
                int(round(rect.height() * dpr))
            ).intersected(QRect(0, 0, self.screen_pixmap.width(), self.screen_pixmap.height()))
            
            cropped_pixmap = self.screen_pixmap.copy(physical_rect)
            
            # Convert QPixmap to PIL Image via QByteArray buffer
            from PyQt6.QtCore import QBuffer, QIODevice
            qbuffer = QBuffer()
            qbuffer.open(QIODevice.OpenModeFlag.ReadWrite)
            cropped_pixmap.save(qbuffer, "PNG")
            bytes_data = bytes(qbuffer.data())
            qbuffer.close()
            
            pil_image = Image.open(io.BytesIO(bytes_data))
            self.snip_captured.emit(pil_image)
            
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 1. Draw the underlying screen screenshot scaled to fit full widget
        if self.screen_pixmap:
            painter.drawPixmap(self.rect(), self.screen_pixmap)
            
        # 2. Draw dark translucent overlay over the whole screen
        painter.fillRect(self.rect(), QColor(10, 15, 25, 140))
        
        # 3. If dragging a selection rectangle, redraw original screen inside the box (clear cut-out)
        rect = self.get_selection_rect()
        if not rect.isEmpty() and self.screen_pixmap:
            dpr = self.screen_dpr
            # Compute matching physical pixel source rectangle to eliminate DPI magnification
            source_rect = QRect(
                int(round(rect.x() * dpr)),
                int(round(rect.y() * dpr)),
                int(round(rect.width() * dpr)),
                int(round(rect.height() * dpr))
            ).intersected(QRect(0, 0, self.screen_pixmap.width(), self.screen_pixmap.height()))
            
            painter.drawPixmap(rect, self.screen_pixmap, source_rect)
            
            # Glowing border around selection
            border_pen = QPen(QColor(0, 190, 255), 2)
            painter.setPen(border_pen)
            painter.drawRect(rect)
            
            # Corner accents
            accent_pen = QPen(QColor(255, 255, 255), 3)
            painter.setPen(accent_pen)
            corner_len = min(12, min(rect.width() // 4, rect.height() // 4))
            
            # Top-left
            painter.drawLine(rect.left(), rect.top(), rect.left() + corner_len, rect.top())
            painter.drawLine(rect.left(), rect.top(), rect.left(), rect.top() + corner_len)
            # Top-right
            painter.drawLine(rect.right(), rect.top(), rect.right() - corner_len, rect.top())
            painter.drawLine(rect.right(), rect.top(), rect.right(), rect.top() + corner_len)
            # Bottom-left
            painter.drawLine(rect.left(), rect.bottom(), rect.left() + corner_len, rect.bottom())
            painter.drawLine(rect.left(), rect.bottom(), rect.left(), rect.bottom() - corner_len)
            # Bottom-right
            painter.drawLine(rect.right(), rect.bottom(), rect.right() - corner_len, rect.bottom())
            painter.drawLine(rect.right(), rect.bottom(), rect.right(), rect.bottom() - corner_len)
            
            # Dimension badge (e.g. 450 × 120 px)
            dim_text = f"{rect.width()} × {rect.height()} px"
            font = QFont("Segoe UI", 9, QFont.Weight.Bold)
            painter.setFont(font)
            badge_w, badge_h = 100, 24
            badge_x = rect.left()
            badge_y = rect.top() - badge_h - 4 if rect.top() >= badge_h + 6 else rect.bottom() + 6
            
            badge_rect = QRect(badge_x, badge_y, badge_w, badge_h)
            painter.setBrush(QBrush(QColor(20, 25, 35, 220)))
            painter.setPen(QPen(QColor(0, 190, 255, 180), 1))
            painter.drawRoundedRect(badge_rect, 4, 4)
            
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, dim_text)
        else:
            # Instruction hint in the top center
            hint_text = "Drag a rectangle to capture text  •  Right-click or ESC to cancel"
            font = QFont("Segoe UI", 11, QFont.Weight.DemiBold)
            painter.setFont(font)
            hint_w, hint_h = 440, 36
            hint_x = (self.width() - hint_w) // 2
            hint_y = 35
            
            hint_rect = QRect(hint_x, hint_y, hint_w, hint_h)
            painter.setBrush(QBrush(QColor(20, 25, 35, 220)))
            painter.setPen(QPen(QColor(0, 190, 255, 150), 1.5))
            painter.drawRoundedRect(hint_rect, 8, 8)
            
            painter.setPen(QColor(230, 240, 255))
            painter.drawText(hint_rect, Qt.AlignmentFlag.AlignCenter, hint_text)
