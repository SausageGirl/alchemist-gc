"""Find images on screen and click them. A generic watcher, separate from the alchemist tasks."""

import time

import pyautogui

from alchemist.input import click_at
from alchemist.platform import is_admin, relaunch_as_admin
from alchemist.vision import find


def run(
    templates: list[str],
    *,
    threshold: float = 0.8,
    interval: float = 1.0,
    loop: bool = False,
    dry_run: bool = False,
    restore_mouse: bool = True,
    admin: bool = False,
) -> None:
    if admin and not is_admin():
        print("Relaunched as administrator in a new window." if relaunch_as_admin() else "Elevation was cancelled.")
        return

    print(f"Admin: {is_admin()}. Starting in 2s. Ctrl+C to stop.")
    time.sleep(2)

    try:
        while True:
            stamp = time.strftime("%H:%M:%S")
            for path in templates:
                match = find(path, threshold)
                if match is None:
                    print(f"[{stamp}] {path}: not found", flush=True)
                    continue
                x, y, score = match
                print(f"[{stamp}] {path}: found at ({x}, {y}) score={score:.2f}", flush=True)
                if not dry_run:
                    original = pyautogui.position()
                    click_at(x, y)
                    if restore_mouse:
                        time.sleep(0.1)
                        pyautogui.moveTo(original)
            if not loop:
                break
            time.sleep(interval)
    except (KeyboardInterrupt, pyautogui.FailSafeException):
        print("Stopped.")
