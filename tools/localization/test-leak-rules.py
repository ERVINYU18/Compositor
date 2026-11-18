#!/usr/bin/env python3
"""Check the leak-detection rules in CompositorUITests/LocalizationLeakTests against fixtures.

The UI test itself needs a real app and a real accessibility layer, so it cannot run here.
Its decision — "is this label English that should have been Chinese?" — is the part that
gets the rule wrong, and that part can be checked against fixtures. The cases below mirror
isLeak(_:) and the allowlist; a compiled fixture branch in CI confirms the whole path.

Exit codes: 0 = the rules behave as specified, 1 = a case is wrong.
"""
import os
import re
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ALLOWLIST = os.path.join(REPO, "tools/localization/ui-allowlist.txt")

# Mirrors `text.range(of: "[A-Za-z]{3,}", options: .regularExpression)`.
RUN_OF_THREE_LETTERS = re.compile(r"[A-Za-z]{3,}")

# A label is translated when it contains a CJK character. Merely being non-ASCII is not
# enough: key symbols and × live in English labels too.
CJK = re.compile("["
                 "\u3000-\u303f"   # CJK punctuation
                 "\u3040-\u30ff"   # kana
                 "\u3400-\u4dbf"   # CJK ext A
                 "\u4e00-\u9fff"   # CJK unified
                 "\uf900-\ufaff"   # compatibility ideographs
                 "\uff00-\uffef"   # fullwidth forms
                 "]")


def allowlist():
    try:
        text = open(ALLOWLIST, encoding="utf-8").read()
    except OSError as e:
        print(f"cannot read {ALLOWLIST}: {e}")
        sys.exit(1)
    return [line.strip() for line in text.splitlines()
            if line.strip() and not line.strip().startswith("#")]


def is_leak(label, allowed):
    """The same decision as the Swift test."""
    text = label.strip()
    if not text:
        return False
    # Translated means it contains a CJK character. Merely being non-ASCII is not enough:
    # "New canvas (⌘N)" is English with a key symbol in it, and must be caught.
    if CJK.search(text):
        return False
    if not RUN_OF_THREE_LETTERS.search(text):
        return False
    # Whole-word match: a bare "T" must not exempt every label containing a t.
    for a in allowed:
        if re.search(r"(?<![A-Za-z0-9])" + re.escape(a) + r"(?![A-Za-z0-9])", text, re.IGNORECASE):
            return False
    return True


# (label, expected leak, why)
CASES = [
    # Real English that must fail — the fourth leak class.
    ("Filter", True, "an AppKit menu title left in English"),
    ("Image Size", True, "a sheet title left in English"),
    ("Cancel", True, "a button left in English"),
    ("Blend mode", True, "a lowercase English accessibility label"),
    ("Undo", True, "a menu item left in English"),
    ("New canvas (⌘N)", True, "a tooltip left in English"),
    ("Cannot open the file", True, "an error message left in English"),

    # Translated: has a Chinese character.
    ("滤镜", False, "translated menu title"),
    ("图像大小", False, "translated sheet title"),
    ("取消", False, "translated button"),
    ("Camera Raw 滤镜", False, "partly translated, still Chinese"),

    # Not words: exempted by §4.5, or too short to be English.
    ("T", False, "the text tool identifier"),
    ("px", False, "a unit"),
    ("100%", False, "a number with its unit"),
    ("⌘N", False, "a keyboard hint"),
    ("1920 × 1080", False, "a dimension"),
    ("PSD", False, "a format acronym, exempted"),
    ("Camera Raw 滤镜", False, "already covered above, kept to prove the allowlist is not needed"),
    ("Generic CMYK Profile", False, "a ColorSync name, exempted by §4.5"),
    ("sRGB", False, "a colour space, exempted"),
    ("Helvetica", False, "a font name, exempted"),

    # Edge cases.
    ("", False, "empty"),
    ("   ", False, "whitespace only"),
    ("AB", False, "two letters is an identifier, not a word"),
]


def main():
    allowed = allowlist()
    print("Localization leak rule fixtures")
    print("=" * 64)
    print(f"allowlist entries: {len(allowed)}")
    print()

    failures = 0
    for label, expected, why in CASES:
        got = is_leak(label, allowed)
        mark = "ok" if got == expected else "FAIL"
        if got != expected:
            failures += 1
        verdict = "leak" if got else "fine"
        print(f'  {mark:4} {verdict:5} {label!r:32} — {why}')

    print()
    if failures == 0:
        print("OK: every fixture is classified as specified.")
    else:
        print(f"FAIL: {failures} fixture(s) classified wrongly.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
