"""Grab a template image: screenshot, drag a box, press Enter."""

import time
from pathlib import Path

import cv2

from alchemist.settings import ROOT
from alchemist.vision import grab_screen

TEMPLATES = ROOT / "templates"


def output_path(name: str) -> Path:
    """Map a template name onto templates/<name>.png, including subfolders."""
    rel = Path(name)
    if rel.is_absolute() or any(part == ".." for part in rel.parts):
        raise SystemExit(f"Template name must stay inside templates/: {name}")
    if rel.suffix.lower() != ".png":
        rel = rel.with_suffix(".png")
    root = TEMPLATES.resolve()
    out = (root / rel).resolve()
    out.relative_to(root)
    return out


def run(name: str, delay: float = 3) -> None:
    print(f"Screenshot in {delay:g}s - switch to the window you want...")
    time.sleep(delay)
    screen = grab_screen()

    window = "Drag a box, then Enter (Esc/c to cancel)"
    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    x, y, w, h = cv2.selectROI(window, screen, showCrosshair=False)
    cv2.destroyAllWindows()

    if w == 0 or h == 0:
        print("Cancelled.")
        return

    out = output_path(name)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), screen[y : y + h, x : x + w])
    print(f"Saved {out} ({w}x{h})")
