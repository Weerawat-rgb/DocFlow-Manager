import sys
import os

def set_window_icon(window):
    """ตั้งค่า icon สำหรับ window ทุกตัว"""
    try:
        if getattr(sys, 'frozen', False):
            window.iconbitmap(sys.executable)
        else:
            icon_path = os.path.join(os.path.dirname(__file__), 'bill.ico')
            window.iconbitmap(icon_path)
    except Exception as e:
        print(f"ไม่สามารถโหลด icon ได้: {e}")