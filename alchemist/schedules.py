"""What the bot gathers and crafts.

Edit the lists here. Item names must match a template image:
  gather:  templates/gather/<name>.png
  craft:   templates/crafting/<name>.png
"""

# (items added in one round, how many rounds in a row)
GATHER_SCHEDULE: list[tuple[list[str], int]] = [
    (["mushroom", "vine"], 2),
    (["calcite", "sand"], 2),
    (["thistle", "pepper", "silica"], 1),
]

# (item, how many times to craft it)
CRAFTS: list[tuple[str, int]] = [
    ("bottle", 2),
    ("hp", 2),
    ("mp", 2),
    ("motor", 2),
]
