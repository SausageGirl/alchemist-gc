"""Open the Gathering Helper and run the gather schedule."""

import time

from alchemist.bot import Bot, StepFailed
from alchemist.schedules import GATHER_SCHEDULE


def open_panel(bot: Bot) -> None:
    bot.open_craft_menu()
    bot.step("gather_menu")
    bot.step("auto_gather")


def wait_round_end(bot: Bot, poll: float, vanish_timeout: float = 30) -> None:
    # end_round is the panel header, so it can still be on screen right after Begin.
    # A notice can cover that header for the whole round, so clear it before trusting the match.
    deadline = time.monotonic() + vanish_timeout
    while True:
        bot.dismiss_interrupts()
        if not bot.visible("end_round"):
            break
        if time.monotonic() > deadline:
            raise StepFailed(
                f"end_round stayed visible {vanish_timeout}s after Begin, so it can't signal the "
                "end of a round. Capture a different end-of-round image with: python -m alchemist capture",
                "end_round",
            )
        time.sleep(1)

    started = time.monotonic()
    while True:
        bot.dismiss_interrupts()
        if bot.visible("end_round"):
            break
        time.sleep(poll)
    bot.log(f"round ended after {(time.monotonic() - started) / 60:.1f} min")


def run_round(bot: Bot, items: list[str], poll: float) -> None:
    bot.click_if_visible("finish")
    added = 0
    for item in items:
        bot.step(f"gather/{item}")
        # When an item is full the confirm button goes transparent / missing — skip it.
        if bot.try_step("confirm", timeout=3):
            added += 1
        else:
            bot.log(f"{item}: confirm not found (full?), skipping")
    if added == 0:
        bot.log("no items added this round (all full?), skipping Begin")
        return
    bot.step("start")
    wait_round_end(bot, poll)


def run(bot: Bot, poll: float = 5) -> None:
    bot.leave_home()
    rounds = [items for items, times in GATHER_SCHEDULE for _ in range(times)]
    open_panel(bot)
    for index, items in enumerate(rounds, 1):
        bot.log(f"round {index}/{len(rounds)}: {', '.join(items)}")
        run_round(bot, items, poll)
    bot.click_if_visible("finish")
    bot.log(f"gathering done: {len(rounds)} rounds")


def check(bot: Bot) -> None:
    names = [
        "leave",
        "close_btn",
        "dont_show_today",
        "durability_check",
        "durability_ignore",
        "event_cancel",
        "expand_menu",
        "craft_menu",
        "gather_menu",
        "auto_gather",
        "confirm",
        "start",
        "finish",
        "end_round",
    ]
    items = [f"gather/{item}" for group, _ in GATHER_SCHEDULE for item in group]
    bot.check_templates(names + items)
