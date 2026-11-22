"""Paths and match settings. Runtime files stay at the project root."""

from dataclasses import dataclass, field
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
ROOT = PACKAGE_DIR.parent


@dataclass
class Settings:
    threshold: float = 0.8
    step_delay: float = 0.8
    templates_dir: Path = field(default_factory=lambda: ROOT / "templates")
    log_file: Path = field(default_factory=lambda: ROOT / "alchemist.log")
    failures_dir: Path = field(default_factory=lambda: ROOT / "failures")
    keep_failure_shots: int = 30
    # The flask sits on the moving world, so it scores under the default 0.8.
    # Catpal still reaches ~0.53 when Crafting is covered, and 0.5 would click the cat.
    threshold_overrides: dict[str, float] = field(default_factory=lambda: {"craft_menu": 0.6})
    # Skip the top of the screen so the Updates HUD button cannot win over craft_menu.
    skip_top_px: dict[str, int] = field(default_factory=lambda: {"craft_menu": 200})
