"""Match the native Windows title bar to the game, when DWM supports it."""

import ctypes
import sys


def apply_dark_titlebar(widget):
    if sys.platform != "win32":
        return False
    try:
        from ctypes import wintypes

        setter = ctypes.windll.dwmapi.DwmSetWindowAttribute
        setter.argtypes = [wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
        setter.restype = ctypes.c_long
        hwnd = int(widget.winId())
        success = False
        # COLORREF is 0x00BBGGRR. Unsupported attributes fail without changing the frame.
        for attribute, value in [(20, 1), (35, 0x002E2723), (36, 0x00E6E6E6), (34, 0x004D433C)]:
            data = wintypes.DWORD(value)
            result = setter(hwnd, attribute, ctypes.byref(data), ctypes.sizeof(data))
            success = success or result == 0
        return success
    except (AttributeError, OSError):
        return False
