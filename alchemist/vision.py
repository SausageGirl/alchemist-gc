"""Screenshot the desktop and locate template images."""

from pathlib import Path

import cv2
import numpy as np

from alchemist.platform import configure_pyautogui, enable_dpi_awareness

# DPI awareness has to be on before pyautogui loads, or clicks land off-target.
enable_dpi_awareness()
import pyautogui

configure_pyautogui()

_templates: dict[tuple[str, float], np.ndarray] = {}


def load_template(path: str | Path, keep_top: float = 1.0) -> np.ndarray:
    """Load a template, optionally keeping only its top fraction (to drop a changing counter)."""
    key = (str(path), keep_top)
    if key not in _templates:
        img = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if img is None:
            raise FileNotFoundError(f"Could not read template image: {path}")
        _templates[key] = img[: max(1, int(img.shape[0] * keep_top))]
    return _templates[key]


def grab_screen(region: tuple[int, int, int, int] | None = None) -> np.ndarray:
    """Screenshot as a BGR array. region = (left, top, width, height)."""
    shot = pyautogui.screenshot(region=region)
    return cv2.cvtColor(np.array(shot), cv2.COLOR_RGB2BGR)


def _match(template_path, region, keep_top):
    template = load_template(template_path, keep_top)
    screen = grab_screen(region)
    th, tw = template.shape[:2]
    if screen.shape[0] < th or screen.shape[1] < tw:
        return None, template
    return cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED), template


def find(template_path, threshold=0.8, region=None, keep_top=1.0):
    """Return (center_x, center_y, score) of the best match, or None."""
    result, template = _match(template_path, region, keep_top)
    if result is None:
        return None
    _, score, _, (x, y) = cv2.minMaxLoc(result)
    if score < threshold:
        return None
    th, tw = template.shape[:2]
    ox, oy = region[:2] if region else (0, 0)
    return ox + x + tw // 2, oy + y + th // 2, score


def find_all(template_path, threshold=0.8, region=None, keep_top=1.0):
    """Return every match as (center_x, center_y, score), best first."""
    result, template = _match(template_path, region, keep_top)
    if result is None:
        return []
    th, tw = template.shape[:2]
    ox, oy = region[:2] if region else (0, 0)

    ys, xs = np.where(result >= threshold)
    candidates = sorted(zip(result[ys, xs], xs, ys), reverse=True)

    # Neighbouring pixels around one real match all score high; keep only the best of each cluster.
    picked = []
    for score, x, y in candidates:
        if all(abs(x - px) > tw // 2 or abs(y - py) > th // 2 for _, px, py in picked):
            picked.append((score, x, y))

    return [(ox + int(x) + tw // 2, oy + int(y) + th // 2, float(s)) for s, x, y in picked]
