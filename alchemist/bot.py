"""Run one screen step at a time: find a template, click it, log the result."""

import time
from collections.abc import Callable
from pathlib import Path

import pyautogui

from alchemist.input import click, click_at
from alchemist.platform import is_admin
from alchemist.settings import ROOT, Settings
from alchemist.vision import find, find_all


class StepFailed(Exception):
    def __init__(self, message: str, name: str | None = None) -> None:
        super().__init__(message)
        self.name = name


class Bot:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        # One tick per notice. A missed Ignore must not click the box again and clear it.
        self._durability_checked = False

    def log(self, msg: str) -> None:
        line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
        print(line, flush=True)
        with open(self.settings.log_file, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    @property
    def step_delay(self) -> float:
        return self.settings.step_delay

    def template(self, name: str) -> Path:
        return self.settings.templates_dir / f"{name}.png"

    def threshold_for(self, name: str) -> float:
        return self.settings.threshold_overrides.get(name, self.settings.threshold)

    def keep_top_for(self, name: str) -> float:
        # Gather item icons show a stock count at the bottom that changes every round.
        return 0.7 if name.startswith("gather/") else 1.0

    def region_for(self, name: str) -> tuple[int, int, int, int] | None:
        skip = self.settings.skip_top_px.get(name)
        if skip is None:
            return None
        width, height = pyautogui.size()
        if skip >= height:
            return None
        return (0, skip, width, height - skip)

    def match_kwargs(self, name: str) -> dict:
        return {
            "threshold": self.threshold_for(name),
            "keep_top": self.keep_top_for(name),
            "region": self.region_for(name),
        }

    def visible(self, name: str) -> bool:
        return find(self.template(name), **self.match_kwargs(name)) is not None

    def wait_for(self, name: str, timeout: float = 10) -> None:
        deadline = time.monotonic() + timeout
        while True:
            self.dismiss_interrupts()
            if self.visible(name):
                return
            if time.monotonic() > deadline:
                raise StepFailed(f"'{name}' did not appear within {timeout}s", name)
            time.sleep(0.5)

    def step(self, name: str, timeout: float = 10, delay: bool = True) -> None:
        if delay:
            time.sleep(self.step_delay)
        if not self._wait_click(name, timeout):
            raise StepFailed(f"'{name}' not found on screen within {timeout}s", name)

    def try_step(self, name: str, timeout: float = 10, delay: bool = True) -> bool:
        """Like step, but return False instead of raising when the template is missing."""
        if delay:
            time.sleep(self.step_delay)
        return self._wait_click(name, timeout)

    def click_if_visible(self, name: str) -> bool:
        time.sleep(self.step_delay)
        self.dismiss_interrupts()
        if click(self.template(name), **self.match_kwargs(name)):
            self.log(f"clicked {name}")
            return True
        return False

    def _wait_click(self, name: str, timeout: float) -> bool:
        deadline = time.monotonic() + timeout
        while True:
            self.dismiss_interrupts()
            if click(self.template(name), **self.match_kwargs(name)):
                self.log(f"clicked {name}")
                return True
            if time.monotonic() >= deadline:
                return False
            time.sleep(0.5)

    def dismiss_interrupts(self) -> None:
        """Close notices that cover gather and craft buttons.

        Broken gear opens a Notice for either tool. Check "Don't show again today"
        once, then Ignore, and leave the gear for the player to replace. A server
        event banner is dismissed with Cancel.
        """
        for _ in range(3):
            if self._dismiss_durability():
                time.sleep(0.4)
                continue
            if self._dismiss_event():
                time.sleep(0.4)
                continue
            return

    def _dismiss_durability(self) -> bool:
        label = find(self.template("dont_show_today"), **self.match_kwargs("dont_show_today"))
        if label is None:
            self._durability_checked = False
            return False
        if not self._durability_checked:
            self._durability_checked = True
            if self._click_durability_checkbox(label):
                self.log("gear durability notice: checked don't show again today")
                time.sleep(0.3)
            else:
                self.log("gear durability notice: checkbox not found")
        if not click(self.template("durability_ignore"), **self.match_kwargs("durability_ignore")):
            raise StepFailed(
                "gear durability notice is up, but Ignore was not found",
                "durability_ignore",
            )
        self.log("clicked durability_ignore")
        return True

    def _click_durability_checkbox(self, label: tuple[int, int, float]) -> bool:
        # The box is the left end of the "Don't show again today" row, ~175px from its center.
        lx, ly, _ = label
        boxes = find_all(self.template("durability_check"), **self.match_kwargs("durability_check"))
        nearby = [box for box in boxes if abs(box[1] - ly) <= 30 and 0 < lx - box[0] <= 260]
        if not nearby:
            return False
        x, y, _ = max(nearby, key=lambda box: box[2])
        click_at(x, y)
        return True

    def _dismiss_event(self) -> bool:
        if not click(self.template("event_cancel"), **self.match_kwargs("event_cancel")):
            return False
        self.log("event notice: clicked Cancel")
        return True

    def close_popups(self, max_clicks: int = 10) -> None:
        """Click close_btn until no close button is left on screen."""
        for _ in range(max_clicks):
            if not self.click_if_visible("close_btn"):
                return
        if self.visible("close_btn"):
            raise StepFailed(f"close_btn still on screen after {max_clicks} clicks", "close_btn")

    def leave_home(self) -> None:
        """Click homestead Leave once. Called at the start of gather and of craft."""
        if not self.click_if_visible("leave"):
            return
        # The round menu is missing until the homestead finishes closing.
        time.sleep(2)

    def open_craft_menu(self) -> None:
        self.close_popups()
        if not self.visible("craft_menu"):
            self.log("craft_menu not visible, expanding menu first")
            self.step("expand_menu")
        self.step("craft_menu")

    def check_templates(self, names: list[str]) -> None:
        """Print how well each template matches the current screen, without clicking."""
        for name in names:
            kwargs = self.match_kwargs(name)
            kwargs["threshold"] = 0  # always report the best score
            match = find(self.template(name), **kwargs)
            if match is None:
                print(f"--  {name:<18} no match")
                continue
            x, y, score = match
            status = "OK " if score >= self.threshold_for(name) else "-- "
            note = f" skip_top={self.settings.skip_top_px[name]}" if name in self.settings.skip_top_px else ""
            print(f"{status} {name:<18} score={score:.2f} at ({x}, {y}){note}")

    def save_failure_shot(self, name: str | None) -> str:
        """Save the screen that stopped the run. Keeps the newest failure shots."""
        self.settings.failures_dir.mkdir(exist_ok=True)
        safe = (name or "unknown").replace("/", "_").replace("\\", "_")
        path = self.settings.failures_dir / f"{time.strftime('%Y-%m-%d_%H%M%S')}_{safe}.png"
        pyautogui.screenshot(str(path))
        shots = sorted(self.settings.failures_dir.glob("*.png"))
        for old in shots[: -self.settings.keep_failure_shots]:
            old.unlink(missing_ok=True)
        return path.relative_to(ROOT).as_posix()

    def failure_score(self, name: str) -> float | None:
        """Best match for the step that failed, even when it is below the click threshold."""
        path = self.template(name)
        if not path.exists():
            return None
        kwargs = self.match_kwargs(name)
        kwargs["threshold"] = -1
        match = find(path, **kwargs)
        return None if match is None else match[2]

    def run_task(self, title: str, task: Callable[[], None], start_delay: float = 3) -> bool:
        """Run a task after a countdown. Failures and Ctrl+C become a log line."""
        try:
            self.log(f"{title}: admin={is_admin()}, starting in {start_delay}s. Ctrl+C to stop.")
            time.sleep(start_delay)
            task()
            return True
        except StepFailed as exc:
            shot = self.save_failure_shot(exc.name)
            score = self.failure_score(exc.name) if exc.name else None
            detail = f", best score={score:.2f}" if score is not None else ""
            self.log(f"{title} stopped: {exc}{detail}; screenshot {shot}")
        except (KeyboardInterrupt, pyautogui.FailSafeException):
            self.log(f"{title} stopped by user")
        return False
