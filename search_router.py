#!/usr/bin/env python3
"""
search_router.py

Decide whether a user question should be answered via:
  - external search (Google / YouTube), or
  - internal recipe knowledge.

This file only does detection + link building.
Use it from main.py like:

    from search_router import route_question

    result = route_question(user_input)
    if result["route"] == "search":
        print("Google:", result["google"])
        print("YouTube:", result["youtube"])
    else:
        # handle internally
        answer = query_internally(...)
"""

import re
import urllib.parse
from typing import Dict, Optional, Tuple

# ---------------------------------------------------------------------
# 1) Patterns for EXTERNAL-LOOKUP questions
# ---------------------------------------------------------------------
# These are the questions where you should return a Google / YouTube link:
#
#   - how to ...          (specific technique)
#   - what is ...         (definitions, including tools)
#   - substitutions       (instead of, sub for, I don't have X)
#   - diet constraints    (gluten-free, dairy-free, etc.)
#   - make-ahead / storage / freeze
#   - troubleshooting     (too thin/thick, burning, not melting)
#   - safety              (safe temperature, is X safe)
#   - general conversions (grams to cups, etc.)
#   - vague "how do I do that"
#
# Everything else should be handled by your internal recipe logic.

REGEX_PATTERNS: Dict[str, re.Pattern] = {
    # Specific "how to" questions
    "ASK_HOWTO_SPECIFIC": re.compile(r"^\s*how\s+to\s+.+", re.I),

    # Definitions ("what is ...")
    "ASK_WHAT_IS": re.compile(r"^\s*what\s+is\s+.+", re.I),

    # Substitutions and missing ingredients
    "ASK_SUB": re.compile(r"(instead of|sub\s+for)\s+.+", re.I),
    "ASK_MISSING": re.compile(r"i\s+don'?t\s+have\s+.+", re.I),

    # Diet/allergy constraints
    "ASK_DIET": re.compile(
        r"(gluten[- ]free|dairy[- ]free|vegan|vegetarian).*(sub|alt|alternative|option)"
        r"|substitute\s+for\s+.+",
        re.I,
    ),

    # Make-ahead, marinating, etc.
    "ASK_AHEAD": re.compile(r"(make.*ahead|marinate.*overnight)", re.I),

    # Storage, freezing, leftovers
    "ASK_STORAGE": re.compile(r"(freeze\s+this|how\s+long.*keep|how\s+long.*last)", re.I),

    # Troubleshooting cooking problems
    "ASK_TROUBLE": re.compile(
        r"(too\s+\w+|burning|not\s+melting|edges\s+burning|sauce\s+too\s+\w+)",
        re.I,
    ),

    # Food safety
    "ASK_SAFETY": re.compile(r"(safe\s+temp|safe\s+temperature|is\s+.+\s+safe)", re.I),

    # General conversions (units)
    "ASK_CONVERT": re.compile(
        r"\b(grams?|g|ml|milliliters?|liters?|l|cups?|c|tablespoons?|tbsp?|teaspoons?|tsp?|oz|ounces?)\b"
        r".*\b(to|in)\b"
        r".*\b(grams?|g|ml|milliliters?|liters?|l|cups?|c|tablespoons?|tbsp?|teaspoons?|tsp?|oz|ounces?)\b",
        re.I,
    ),

    # Tool questions / definitions
    "ASK_TOOL": re.compile(r"^\s*what\s+is\s+a\s+.+", re.I),

    # Tool substitutions
    "ASK_TOOL_SUB": re.compile(r"^\s*no\s+\w+.*(what\s+can\s+i\s+use|instead)", re.I),

    # Pan size, etc.
    "ASK_SIZE": re.compile(
        r"(what\s+size\s+\w+|^\s*(8x8|9x9|9x13|12-inch|10-inch|11x7)\s+ok\??)",
        re.I,
    ),

    # Vague "how do I do that"
    "ASK_HOWTO_VAGUE": re.compile(
        r"^\s*how\s+(do|should)\s+i\s+(do\s+that|do\s+it)\??\s*$",
        re.I,
    ),
}

EXTERNAL_LOOKUP_INTENTS = set(REGEX_PATTERNS.keys())


# ---------------------------------------------------------------------
# 2) Classification
# ---------------------------------------------------------------------
def classify_external_lookup(user_text: str) -> Tuple[bool, Optional[str]]:
    """
    Decide if this question needs an external search.

    Returns:
        (is_search, intent_name or None)
    """
    for intent, pat in REGEX_PATTERNS.items():
        if pat.search(user_text):
            return True, intent
    return False, None


# ---------------------------------------------------------------------
# 3) Query and link builders
# ---------------------------------------------------------------------
def build_query(user_text: str) -> str:
    """
    Build a search query string for Google / YouTube.
    We mostly keep the question as-is and just normalize spaces.
    """
    q = re.sub(r"\s+", " ", user_text.strip())
    return urllib.parse.quote_plus(q)


def build_links(query: str) -> Dict[str, str]:
    return {
        "google": f"https://www.google.com/search?q={query}",
        "youtube": f"https://www.youtube.com/results?search_query={query}",
    }


# ---------------------------------------------------------------------
# 4) Public API
# ---------------------------------------------------------------------
def route_question(user_text: str) -> Dict[str, Optional[str]]:
    """
    Main entry point.

    Args:
        user_text: the raw question from terminal/GUI (string).

    Returns:
        {
          "route": "search" or "recipe",
          "intent": intent_name or None,
          "google": url or None,
          "youtube": url or None,
        }
    """
    is_search, intent = classify_external_lookup(user_text)
    if is_search:
        q = build_query(user_text)
        links = build_links(q)
        return {
            "route": "search",
            "intent": intent,
            "google": links["google"],
            "youtube": links["youtube"],
        }

    # If not matched as external, treat it as recipe-grounded.
    return {
        "route": "recipe",
        "intent": None,
        "google": None,
        "youtube": None,
    }


# ---------------------------------------------------------------------
# 5) Simple CLI for testing
# ---------------------------------------------------------------------
def main():
    print("Question router (type Ctrl+C to exit).")
    while True:
        try:
            text = input("> ").strip()
            if not text:
                continue
            result = route_question(text)
            if result["route"] == "search":
                print(f"[SEARCH] intent={result['intent']}")
                print("  Google :", result["google"])
                print("  YouTube:", result["youtube"])
            else:
                print("[RECIPE] handle this from internal recipe data.")
        except (KeyboardInterrupt, EOFError):
            print("\nBye!")
            break


if __name__ == "__main__":
    main()
