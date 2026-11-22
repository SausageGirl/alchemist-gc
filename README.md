# Alchemist helper

Clicks through the Tree of Savior: Neverland alchemist for you: gathering, crafting, or both on a loop. It matches screenshots in `templates/` and clicks them.

Windows only. Needs Python 3.11+.

## Install

From this folder:

```bat
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run

Double-click `start.bat`, or:

```bat
.venv\Scripts\python.exe -m alchemist
```

The menu asks for administrator because the game runs as administrator. Pick a number:

1. Gathering
2. Crafting
3. Gather, then craft, forever
4. Craft, then gather, forever
5. Check templates (no clicking)

Stop with Ctrl+C, or shove the mouse into a screen corner.

One job, without the menu:

```bat
.venv\Scripts\python.exe -m alchemist gather --admin
.venv\Scripts\python.exe -m alchemist craft --admin
.venv\Scripts\python.exe -m alchemist gather --check
```

`--check` prints how well each image matches the current screen and does not click.

## Change what it farms

Edit the lists in `alchemist/schedules.py`. Each name needs a PNG:

- gather: `templates/gather/<name>.png`
- craft: `templates/crafting/<name>.png`

To grab a new image, open the game on that screen, then drag a box around the icon:

```bat
.venv\Scripts\python.exe -m alchemist capture gather/mushroom
```

Runs are appended to `alchemist.log`. If a step fails, a screenshot lands in `failures/`.
