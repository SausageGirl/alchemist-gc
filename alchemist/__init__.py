"""Tree of Savior: Neverland alchemist helper."""

from alchemist.platform import enable_dpi_awareness

# Must run before pyautogui is imported, or Windows display scaling
# makes screenshot pixels and mouse coordinates disagree.
enable_dpi_awareness()
