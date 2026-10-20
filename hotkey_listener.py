"""
Global Hotkey Listener for Windows using native Win32 API.
Allows triggering the screen snip overlay anywhere (even if the app is minimized or backgrounded).
Default hotkey: Ctrl + Alt + S
"""
import ctypes
from ctypes import wintypes
import time
from PyQt6.QtCore import QThread, pyqtSignal

# Win32 Constants
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312

class GlobalHotkeyThread(QThread):
    hotkey_triggered = pyqtSignal()
    
    def __init__(self, key_vk=0x53, modifiers=(MOD_CONTROL | MOD_ALT)):
        """
        Default: 0x53 is 'S' key. Modifiers: Ctrl + Alt.
        """
        super().__init__()
        self.key_vk = key_vk
        self.modifiers = modifiers | MOD_NOREPEAT
        self.running = True
        self.hotkey_id = 99
        
    def run(self):
        user32 = ctypes.windll.user32
        
        # Register the hotkey
        res = user32.RegisterHotKey(None, self.hotkey_id, self.modifiers, self.key_vk)
        if not res:
            # Try without MOD_NOREPEAT in case of older Win32 compatibility
            res = user32.RegisterHotKey(None, self.hotkey_id, self.modifiers & ~MOD_NOREPEAT, self.key_vk)
            
        msg = wintypes.MSG()
        while self.running:
            # PeekMessage or GetMessage to process hotkey events
            if user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):  # PM_REMOVE = 1
                if msg.message == WM_HOTKEY and msg.wParam == self.hotkey_id:
                    self.hotkey_triggered.emit()
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
            time.sleep(0.05)
            
        user32.UnregisterHotKey(None, self.hotkey_id)
        
    def stop(self):
        self.running = False
        self.wait(1000)
