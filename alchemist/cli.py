"""Command line: menu by default, or one task directly."""

import argparse
from collections.abc import Callable

from alchemist.bot import Bot
from alchemist.platform import is_admin, relaunch_as_admin
from alchemist.settings import Settings
from alchemist.tasks import craft, gather
from alchemist.tools import capture, click


def gather_craft_loop(bot: Bot) -> None:
    """Gather, then craft, forever. Ctrl+C or any failed step stops it."""
    cycle = 0
    while True:
        cycle += 1
        bot.log(f"=== cycle {cycle}: gathering ===")
        gather.run(bot)
        bot.log(f"=== cycle {cycle}: crafting ===")
        craft.run(bot)


def craft_gather_loop(bot: Bot) -> None:
    """Craft, then gather, forever. Ctrl+C or any failed step stops it."""
    cycle = 0
    while True:
        cycle += 1
        bot.log(f"=== cycle {cycle}: crafting ===")
        craft.run(bot)
        bot.log(f"=== cycle {cycle}: gathering ===")
        gather.run(bot)


TASKS: dict[str, tuple[str, Callable[[Bot], None]]] = {
    "1": ("Gathering", lambda bot: gather.run(bot)),
    "2": ("Crafting", lambda bot: craft.run(bot)),
    "3": ("Gather + Craft loop", gather_craft_loop),
    "4": ("Craft + Gather loop", craft_gather_loop),
}

MENU = """
=== Alchemist helper ===
  1) Gathering
  2) Crafting
  3) Loop: Gathering -> Crafting -> repeat
  4) Loop: Crafting -> Gathering -> repeat
  5) Check templates (no clicking)
  6) Capture a template (drag a box)
  q) Quit
"""


def run_menu() -> None:
    if not is_admin():
        print("Relaunched as administrator in a new window." if relaunch_as_admin() else "Elevation was cancelled.")
        return

    bot = Bot()
    while True:
        print(MENU)
        try:
            choice = input("Pick: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            return

        if choice == "q":
            return
        if choice == "5":
            print("\n-- gathering --")
            gather.check(bot)
            print("\n-- crafting --")
            craft.check(bot)
        elif choice == "6":
            name = input("Template name (e.g. gather/mushroom): ").strip()
            if not name:
                print("No name given, nothing saved.")
                continue
            try:
                capture.run(name, delay=3)
            except SystemExit as exc:
                print(exc)
        elif choice in TASKS:
            title, task = TASKS[choice]
            bot.run_task(title, lambda task=task: task(bot))
        else:
            print("Type 1, 2, 3, 4, 5, 6 or q.")


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("-t", "--threshold", type=float, default=0.8)
    parser.add_argument("--delay", type=float, default=0.8, help="seconds to wait before every click")
    parser.add_argument(
        "--admin",
        action="store_true",
        help="relaunch elevated; needed because the game runs as administrator",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="alchemist",
        description="Tree of Savior: Neverland alchemist helper.",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("menu", help="interactive menu (this is the default)")

    gather_parser = sub.add_parser("gather", help="run the gathering schedule")
    _add_common(gather_parser)
    gather_parser.add_argument("--poll", type=float, default=5, help="seconds between end-of-round checks")
    gather_parser.add_argument("--check", action="store_true", help="print template match scores and exit")

    craft_parser = sub.add_parser("craft", help="run the crafting schedule")
    _add_common(craft_parser)
    craft_parser.add_argument("--poll", type=float, default=5, help="seconds between craft-finished checks")
    craft_parser.add_argument("--check", action="store_true", help="print template match scores and exit")

    capture_parser = sub.add_parser("capture", help="grab a template image from the screen")
    capture_parser.add_argument("name", help="file to save, e.g. ok_button or gather/mushroom")
    capture_parser.add_argument("--delay", type=float, default=3, help="seconds before the screenshot")

    click_parser = sub.add_parser("click", help="find images on screen and click them")
    click_parser.add_argument("templates", nargs="+", help="image(s) to look for, e.g. templates/ok.png")
    click_parser.add_argument("-t", "--threshold", type=float, default=0.8)
    click_parser.add_argument("-i", "--interval", type=float, default=1.0, help="seconds between scans")
    click_parser.add_argument("--loop", action="store_true", help="keep scanning until Ctrl+C")
    click_parser.add_argument("--dry-run", action="store_true", help="report matches but don't click")
    click_parser.add_argument(
        "--no-restore-mouse",
        dest="restore_mouse",
        action="store_false",
        help="leave the cursor on the clicked spot instead of moving it back",
    )
    click_parser.add_argument(
        "--admin",
        action="store_true",
        help="relaunch elevated; needed when the target app runs as administrator",
    )
    return parser


def _run_flow(title: str, args: argparse.Namespace, run, check) -> None:
    if args.admin and not args.check and not is_admin():
        print("Relaunched as administrator in a new window." if relaunch_as_admin() else "Elevation was cancelled.")
        return
    bot = Bot(Settings(threshold=args.threshold, step_delay=args.delay))
    if args.check:
        check(bot)
        return
    ok = bot.run_task(title, lambda: run(bot, args.poll))
    raise SystemExit(0 if ok else 1)


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if args.command == "gather":
        _run_flow("Gathering", args, gather.run, gather.check)
    elif args.command == "craft":
        _run_flow("Crafting", args, craft.run, craft.check)
    elif args.command == "capture":
        capture.run(args.name, args.delay)
    elif args.command == "click":
        click.run(
            args.templates,
            threshold=args.threshold,
            interval=args.interval,
            loop=args.loop,
            dry_run=args.dry_run,
            restore_mouse=args.restore_mouse,
            admin=args.admin,
        )
    else:
        run_menu()
