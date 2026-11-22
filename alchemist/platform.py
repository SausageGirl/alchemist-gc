"""Windows process setup: per-monitor DPI and an elevated relaunch."""

import ctypes
import subprocess
import sys

from alchemist.settings import ROOT


def enable_dpi_awareness() -> None:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        pass


def configure_pyautogui() -> None:
    import pyautogui

    pyautogui.FAILSAFE = True  # move the mouse into a screen corner to abort
    pyautogui.PAUSE = 0.05


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except (AttributeError, OSError):
        return False


def relaunch_as_admin() -> bool:
    """Re-run `python -m alchemist` elevated. The new console stays open after it exits."""
    extra = subprocess.list2cmdline(sys.argv[1:])
    params = f'/k cd /d "{ROOT}" && "{sys.executable}" -m alchemist {extra}'
    rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe", params, None, 1)
    return rc > 32
