"""Open the Alchemy page and craft the schedule at max quantity."""

import time

from alchemist.bot import Bot, StepFailed
from alchemist.schedules import CRAFTS

# Seconds the Alchemy page gets to close after Make before we call it a failure.
PAGE_CLOSE_GRACE = 1
# A popup can cover the flask, or the game can drop the click. Try again after closing it.
OPEN_ATTEMPTS = 3


def open_page(bot: Bot) -> None:
    failure = None
    for attempt in range(1, OPEN_ATTEMPTS + 1):
        try:
            bot.open_craft_menu()
            bot.wait_for("crafting_page")
        except StepFailed as exc:
            failure = exc
            if attempt == OPEN_ATTEMPTS:
                break
            bot.log(
                f"alchemy page did not open ({attempt}/{OPEN_ATTEMPTS}), "
                "closing popups and trying again"
            )
            bot.close_popups()
            continue
        bot.log("alchemy page open")
        return
    raise failure


def wait_craft_done(bot: Bot, poll: float) -> None:
    # A successful Make closes the Alchemy page; it comes back when the craft finishes.
    # A notice can cover the page for the whole craft, so clear it before trusting the match.
    started = time.monotonic()
    while True:
        bot.dismiss_interrupts()
        if bot.visible("crafting_page"):
            break
        time.sleep(poll)
    bot.log(f"craft finished after {(time.monotonic() - started) / 60:.1f} min")


def page_closed(bot: Bot) -> bool:
    bot.dismiss_interrupts()
    deadline = time.monotonic() + PAGE_CLOSE_GRACE
    while bot.visible("crafting_page"):
        if time.monotonic() > deadline:
            return False
    return True


def craft_once(bot: Bot, item: str, poll: float) -> bool:
    """Craft one batch. Returns False when Make did not go through."""
    bot.step(f"crafting/{item}")
    time.sleep(bot.step_delay)
    bot.dismiss_interrupts()
    if bot.visible("max_craft_disable"):
        bot.log(f"{item}: max button is disabled, skipping")
        return False
    bot.step("max_craft", delay=False)
    bot.step("start_craft")
    if not page_closed(bot):
        bot.log(f"{item}: Alchemy page is still open, can't craft it (out of materials?), moving on")
        bot.click_if_visible("max_craft")
        return False
    wait_craft_done(bot, poll)
    return True


def run(bot: Bot, poll: float = 5) -> None:
    bot.leave_home()
    jobs = [item for item, times in CRAFTS for _ in range(times)]
    open_page(bot)
    crafted = 0
    for index, item in enumerate(jobs, 1):
        bot.log(f"craft {index}/{len(jobs)}: {item}")
        crafted += craft_once(bot, item, poll)
    bot.log(f"crafting done: {crafted}/{len(jobs)} crafted, {len(jobs) - crafted} skipped")


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
        "crafting_page",
        "max_craft",
        "max_craft_disable",
        "start_craft",
    ]
    items = [f"crafting/{item}" for item, _ in CRAFTS]
    bot.check_templates(names + items)
