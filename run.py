"""
OmniScan OCR — Main Application Launcher.
Initializes the GUI, System Tray, Global Hotkey listener, and Window instances.
"""
import sys
import os

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Force unbuffered output so status prints immediately to console
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(line_buffering=True, encoding="utf-8")
        sys.stderr.reconfigure(line_buffering=True, encoding="utf-8")
    except Exception:
        pass

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QFont
from PyQt6.QtCore import Qt

from main_window import MainWindow
from hotkey_listener import GlobalHotkeyThread

def create_default_tray_icon():
    """Generate a clean vector icon pixmap for system tray."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # Outer circle
    painter.setBrush(QColor(14, 165, 233))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(4, 4, 56, 56, 16, 16)
    
    # Inner Letter 'O'
    painter.setPen(QColor(255, 255, 255))
    font = QFont("Segoe UI", 26, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "O")
    painter.end()
    
    return QIcon(pixmap)

def main():
    print("=" * 60)
    print("           Starting OmniScan OCR Studio...           ")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    app.setApplicationName("OmniScan OCR")
    app.setQuitOnLastWindowClosed(True)
    
    app_icon = create_default_tray_icon()
    app.setWindowIcon(app_icon)
    
    # Main Window
    print("[1/4] Initializing Main Studio Window...")
    window = MainWindow()
    window.setWindowIcon(app_icon)
    
    # Center on screen
    screen_geo = app.primaryScreen().availableGeometry()
    x = max(0, (screen_geo.width() - window.width()) // 2)
    y = max(0, (screen_geo.height() - window.height()) // 2)
    window.move(x, y)
    
    window.showNormal()
    window.raise_()
    window.activateWindow()
    
    try:
        import ctypes
        hwnd = int(window.winId())
        user32 = ctypes.windll.user32
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        user32.SetForegroundWindow(hwnd)
    except Exception:
        pass
        
    print("[2/4] Main Studio Window displayed on screen.")
    
    # System Tray Icon
    tray_icon = QSystemTrayIcon(app_icon, app)
    tray_icon.setToolTip("OmniScan OCR (Press Ctrl+Alt+S to Snip)")
    
    tray_menu = QMenu()
    
    action_snip = QAction("✂ Snip Screen Area (Ctrl+Alt+S)", tray_menu)
    action_snip.triggered.connect(window.start_snip)
    tray_menu.addAction(action_snip)
    
    action_pdf = QAction("📄 PDF Document OCR", tray_menu)
    action_pdf.triggered.connect(window.open_pdf_tab)
    tray_menu.addAction(action_pdf)
    
    action_img = QAction("🖼️ Image OCR", tray_menu)
    action_img.triggered.connect(window.open_image_tab)
    tray_menu.addAction(action_img)
    
    tray_menu.addSeparator()
    
    action_show = QAction("⛶ Open OCR Studio", tray_menu)
    action_show.triggered.connect(window.show_and_activate)
    tray_menu.addAction(action_show)
    
    action_toggle_bar = QAction("📌 Toggle Floating Bar", tray_menu)
    action_toggle_bar.triggered.connect(lambda: window.chk_floating.setChecked(not window.chk_floating.isChecked()))
    tray_menu.addAction(action_toggle_bar)
    
    tray_menu.addSeparator()
    
    action_exit = QAction("✕ Exit", tray_menu)
    tray_menu.addAction(action_exit)
    
    tray_icon.setContextMenu(tray_menu)
    tray_icon.show()
    print("[3/4] System Tray Icon ready.")
    
    # Start Global Hotkey Thread (Ctrl+Alt+S)
    print("[4/4] Registering Global Hotkey (Ctrl + Alt + S)...")
    hotkey_thread = GlobalHotkeyThread()
    hotkey_thread.hotkey_triggered.connect(window.start_snip)
    window.hotkey_thread = hotkey_thread
    hotkey_thread.start()
    
    def exit_app():
        print("[OmniScan] Exiting application cleanly...")
        hotkey_thread.stop()
        app.quit()
        
    action_exit.triggered.connect(exit_app)
    
    print("=" * 60)
    print("OmniScan OCR Studio is ACTIVE and RUNNING on your screen!")
    print("Press Ctrl + Alt + S anywhere to snip screen text.")
    print("=" * 60)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
