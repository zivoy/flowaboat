import os

import regex

if not os.path.exists("./config"):
    os.mkdir("./config")

SEPARATOR = "※"  # "✦"

DIGITS = regex.compile(r"^\D+(\d+)$")

DATE_FORM = "YYYY-MM-DD hh:mm:ss"

__all__ = ["config", "discord", "utils", "DATE_FORM", "DIGITS", "SEPARATOR", "errors"]
