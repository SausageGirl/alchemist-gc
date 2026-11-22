# Alchemist — structure and how to change it

Screen automation for the Tree of Savior: Neverland alchemist. It finds a template image on the desktop and clicks it. Python 3.11+. Run from the repo root with the local venv:

```bat
start.bat
.venv\Scripts\python.exe -m alchemist
```

Read this file before adding a feature. Keep the layers below. Do not put new scripts back at the repo root.

## Layers

Each layer may call the ones under it. A task never calls OpenCV, pyautogui, or `vision.find` itself.

| Layer | File | Owns |
|---|---|---|
| Entry | `alchemist/cli.py`, `alchemist/__main__.py`, `start.bat` | Menu, subcommands, admin relaunch for a run |
| Tasks | `alchemist/tasks/` | Game flow: which button, in which order, when to skip |
| Schedules | `alchemist/schedules.py` | What to gather and craft. This is the file the user edits most |
| Step runner | `alchemist/bot.py` | One step: wait, find template, click, log. `StepFailed` |
| Settings | `alchemist/settings.py` | Thresholds, click delay, paths |
| Input | `alchemist/input.py` | Mouse move and held click |
| Vision | `alchemist/vision.py` | Screenshot and template match |
| Platform | `alchemist/platform.py` | DPI awareness, “am I admin”, elevated relaunch |
| Tools | `alchemist/tools/` | Capture a template, or click an arbitrary image. Not part of gather/craft |

```
cli  →  tasks  →  bot  →  input  →  vision
                  ↑         ↘
            schedules    platform
            settings
```

`templates/` stays at the repo root, next to the package. Runtime output stays there too: `alchemist.log` and `failures/`. Both are gitignored, along with `.venv/`.

## Commands

| Intent | Command |
|---|---|
| Menu (asks for admin) | `python -m alchemist` |
| Gather schedule | `python -m alchemist gather --admin` |
| Craft schedule | `python -m alchemist craft --admin` |
| Print match scores, no clicks | `python -m alchemist gather --check` |
| Save a template | `python -m alchemist capture gather/mushroom` |
| Click any image | `python -m alchemist click templates/ok.png --admin` |

The menu always relaunches elevated, because the game runs as administrator. `gather` and `craft` elevate only when passed `--admin`. `--check` never clicks and never relaunches.

Move the mouse into a screen corner to abort (`pyautogui.FAILSAFE`).

## Where a change goes

| Change | Edit |
|---|---|
| Add or remove a gather item, or how many rounds | `schedules.py` `GATHER_SCHEDULE`, and a PNG at `templates/gather/<name>.png` |
| Add or remove a craft | `schedules.py` `CRAFTS`, and `templates/crafting/<name>.png` |
| Order of clicks, skip rules, waits | `alchemist/tasks/gather.py` or `craft.py` |
| New game workflow (a third loop) | New module in `alchemist/tasks/`, then a menu row and subcommand in `cli.py` |
| Default match confidence or delay | `Settings` in `settings.py` |
| One template needs a lower score, or must ignore the top of the screen | `threshold_overrides` or `skip_top_px` in `Settings` |
| Click is missed by the game, or the cursor jumps | `input.py` only |
| Match finds the wrong icon | `vision.py`, or a new template. Do not special-case coordinates inside a task |
| Log line or failure screenshot | `bot.py` |

A template name is a path without `.png`. `bot.step("gather/mushroom")` loads `templates/gather/mushroom.png`. Capture with the same relative name:

```bat
python -m alchemist capture gather/mushroom
python -m alchemist capture crafting/hp
```

Names starting with `gather/` keep only the top 70% of the image, because the stock count on the bottom changes every round. `craft_menu` uses threshold `0.7` and ignores the top 200px so the Updates HUD button cannot win. Other round-menu icons such as Catpal score about 0.53, so a covered Crafting button is a miss instead of a click on the wrong icon.

Broken gear opens a Notice over gather or craft. `dont_show_today` is the checkbox row, `durability_check` is the box, and `durability_ignore` is Ignore. The bot ticks the box once and clicks Ignore, and leaves the gear for the player to replace. A server event banner is `event_cancel`. `Bot.dismiss_interrupts` clears both while a step or a round is waiting. Homestead `leave` is separate: `leave_home` clicks it once when gather or craft starts, then waits for the homestead to close.

## How to write a task

A task is a function that receives a `Bot`. It describes the game. It does not search the screen itself.

```python
from alchemist.bot import Bot, StepFailed

def run(bot: Bot, poll: float = 5) -> None:
    bot.step("some_button")          # wait, click, log. Raises StepFailed if missing.
    if not bot.try_step("confirm", timeout=3):
        bot.log("confirm missing, skipping")
        return
    bot.wait_for("done_banner", timeout=30)
```

Use these `Bot` methods from tasks:

| Method | Behavior |
|---|---|
| `step(name, timeout=10, delay=True)` | Sleep `step_delay`, then click. Raise `StepFailed` if it never appears |
| `try_step(name, timeout=10)` | Same click, return `False` instead of raising |
| `click_if_visible(name)` | One attempt after the delay. `False` if absent |
| `visible(name)` | Match only, no click |
| `wait_for(name, timeout=10)` | Poll until visible, then raise `StepFailed` |
| `open_craft_menu()` | Close popups, expand the menu if needed, click Craft |
| `dismiss_interrupts()` | Tick "Don't show again today" and Ignore a gear notice, or Cancel an event banner |
| `leave_home()` | Click homestead Leave once, at the start of gather and of craft |
| `log(msg)` | Console and `alchemist.log` |
| `check_templates(names)` | Print scores. Used by `--check`. Does not click |

Raise `StepFailed("why", "template_name")` for a dead end. The second argument is the template name. `run_task` then saves `failures/<time>_<name>.png` and logs the best score, including scores below the click threshold. `run_task` already catches `StepFailed`, `KeyboardInterrupt`, and the failsafe. Tasks should let those propagate. Loops in `cli.py` rely on that: one failed step stops the cycle.

Shared clicks used by more than one task belong on `Bot` (see `open_craft_menu`). A click used by one workflow stays in that task file.

Wire a new task like gather and craft:

1. `alchemist/tasks/<name>.py` with `run(bot, poll=5)` and `check(bot)`.
2. Menu entry in `TASKS` in `cli.py`.
3. Subparser in `build_parser`, handled in `main` via `_run_flow`.
4. Pass settings in from the CLI. Do not read `sys.argv` inside the task, and do not store threshold or delay on the module.

```python
bot = Bot(Settings(threshold=args.threshold, step_delay=args.delay))
bot.run_task("Title", lambda: my_task.run(bot, args.poll))
```

## Rules that are easy to break

- Set DPI awareness before pyautogui is imported. `alchemist/__init__.py` and `vision.py` already do this. A new module that imports pyautogui at import time must not run before that, or clicks land in the wrong place on scaled displays.
- Clicks are held (`mouseDown`, sleep, `mouseUp` in `input.click_at`). The game drops an instant down/up pair. Do not replace this with `pyautogui.click`.
- `step_delay` (default 0.8s) runs before a click so a menu can finish animating. Skip it only with `delay=False` when the previous step already waited, as `max_craft` does.
- Match policy stays in `Bot.match_kwargs` (`threshold_for`, `keep_top_for`, `region_for`). Tasks pass a template name, not a raw threshold.
- `relaunch_as_admin` starts `python -m alchemist` with the same extra arguments, from the repo root. Keep that command shape.
- Dependencies live in both `requirements.txt` and `pyproject.toml`. Update both.
- Comments should record a game quirk (why `end_round` is ignored right after Begin, why a button goes transparent when full). Do not comment the obvious.

## Check without playing

Import and CLI help are safe. `--check` screenshots the desktop but does not click. A real gather or craft run moves the mouse, so do not start one just to see if the code imports.

```bat
.venv\Scripts\python.exe -m compileall -q alchemist
.venv\Scripts\python.exe -m alchemist gather --help
```
