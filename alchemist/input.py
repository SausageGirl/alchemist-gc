"""Mouse clicks. Games miss an instant down/up pair, so each click is held briefly."""

import time

import pyautogui

from alchemist.platform import configure_pyautogui
from alchemist.vision import find

configure_pyautogui()


def click_at(x, y, button="left", hold=0.08, settle=0.05):
    pyautogui.moveTo(x, y)
    time.sleep(settle)
    pyautogui.mouseDown(button=button)
    time.sleep(hold)
    pyautogui.mouseUp(button=button)
    time.sleep(settle)


def click(template_path, threshold=0.8, region=None, button="left", keep_top=1.0):
    """Click the best match once. Returns True if something was clicked."""
    match = find(template_path, threshold, region, keep_top)
    if match is None:
        return False
    x, y, _ = match
    click_at(x, y, button=button)
    return True


def wait_and_click(template_path, timeout=10.0, interval=0.5, **kwargs):
    """Keep looking until the image shows up, then click it."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if click(template_path, **kwargs):
            return True
        time.sleep(interval)
    return False
