#!/usr/bin/env python3
"""
search_router.py
Classify a user input (string) as requiring an external lookup (Google/YouTube)
based on a small Context-Free Grammar (CFG) and regex fallbacks. If it requires
a search, output Google and YouTube URLs; otherwise say it's recipe-grounded.

Usage (interactive):
    python search_router.py
    > how to saute onions
    [SEARCH] google: https://www.google.com/search?q=how+to+saute+onions
             youtube: https://www.youtube.com/results?search_query=how+to+saute+onions

Dependencies:
    pip install nltk
(No NLTK corpora downloads are required for CFG parsing.)
"""

import re
import sys
import urllib.parse
from typing import Optional, Dict, Tuple

try:
    # nltk is only used for a simple grammar-based recognizer
    import nltk
    from nltk import CFG
    from nltk.parse import EarleyChartParser
except ImportError as e:
    print("Please install nltk: pip install nltk", file=sys.stderr)
    raise


# --------------------------
# 1) CFG: External-Lookup intents
# --------------------------
# We design a small grammar that recognizes question *shapes* associated with external lookup:
#   - ASK_HOWTO_SPECIFIC: "how to <phrase>"
#   - ASK_WHAT_IS: "what is <term>"
#   - ASK_SUB: "what can i use instead of <ingredient>" / "sub for <ingredient>"
#   - ASK_MISSING: "i don't have <ingredient> what can i use"
#   - ASK_DIET: "<constraint> alternative/substitute (for) <ingredient>"
#   - ASK_AHEAD: "can i make this ahead" / "marinate overnight"
#   - ASK_STORAGE: "how long does it keep" / "can i freeze this"
#   - ASK_TROUBLE: "<component> too <issue>" / "edges burning" / "not melting"
#   - ASK_SAFETY: "safe temp for <ingredient>" / "is <food> safe"
#   - ASK_CONVERT (general): "grams to cups" etc. (we treat non-trivial unit conversions as external)
#   - ASK_TOOL: "what is a <tool>"
#   - ASK_TOOL_SUB: "no <tool> what can i use"
#   - ASK_SIZE: "what size pan", "9x13 ok?"
#   - ASK_HOWTO_VAGUE: "how do i do that" (we still search externally for the resolved target)
#
# The grammar is intentionally permissive: it accepts broad token categories like WORD to
# avoid over-fitting to exact phrasing, then we map top rule → external lookup.

GRAMMAR = r"""
S -> HOWTO_SPEC
S -> WHATIS
S -> SUBSTITUTE
S -> MISSING
S -> DIET
S -> AHEAD_Q
S -> STORAGE
S -> TROUBLE
S -> SAFETY
S -> CONVERT
S -> TOOL_DEF
S -> TOOL_SUB
S -> SIZE
S -> HOWTO_VAGUE

HOWTO_SPEC -> HOW TO PHRASE
WHATIS    -> WHAT IS PHRASE

SUBSTITUTE -> WHAT_CAN_I_USE_INSTEAD_OF PHRASE
SUBSTITUTE -> SUB_FOR PHRASE

MISSING   -> I_DONT_HAVE PHRASE WHAT CAN I USE

DIET      -> CONSTRAINT ALT FOR PHRASE

AHEAD_Q     -> CAN_I_MAKE_THIS_AHEAD
AHEAD_Q     -> MARINATE_OVERNIGHT

STORAGE   -> HOW_LONG_DOES_IT_KEEP
STORAGE   -> CAN_I_FREEZE_THIS

TROUBLE   -> PHRASE TOO ISSUE
TROUBLE   -> ISSUE PHRASE

SAFETY    -> SAFE_TEMP_FOR PHRASE
SAFETY    -> IS_PHRASE_SAFE

CONVERT   -> PHRASE TO PHRASE

TOOL_DEF  -> WHAT_IS_A PHRASE
TOOL_SUB  -> NO PHRASE WHAT CAN I USE

SIZE      -> WHAT_SIZE PHRASE
SIZE      -> SIZE_NUMBER OK

# ----- Lexical -----

HOW -> 'how'
TO -> 'to'
WHAT -> 'what'
IS -> 'is'
A -> 'a'
CAN -> 'can'
I -> 'i'
USE -> 'use'
INSTEAD -> 'instead'
OF -> 'of'
SUB -> 'sub'
FOR -> 'for'
DONT -> "don't"
HAVE -> 'have'

CONSTRAINT -> 'gluten-free' | 'dairy-free' | 'vegetarian' | 'vegan'
ALT -> 'alternative' | 'substitute' | 'option'

MAKE -> 'make'
THIS -> 'this'
AHEAD -> 'ahead'

MARINATE -> 'marinate'
OVERNIGHT -> 'overnight'

HOW_LONG -> 'how' 'long'
DOES -> 'does'
IT -> 'it'
KEEP -> 'keep'

FREEZE -> 'freeze'

SAFE -> 'safe'
TEMP -> 'temp' | 'temperature'

NO -> 'no'
OK -> 'ok'

PHRASE -> PHRASE WORD | WORD

ISSUE -> 'thin' | 'thick' | 'burning' | 'sticky' | 'dry' | 'watery' | 'salty' | 'bland' | 'not' 'melting'

SIZE_NUMBER -> '8x8' | '9x9' | '9x13' | '12-inch' | '10-inch' | '11x7'

WORD -> /[a-zA-Z0-9+\-°]+/

# ----- Fixed multi-token nonterminals -----

HOW_LONG_DOES_IT_KEEP -> 'how' 'long' 'does' 'it' 'keep'
CAN_I_FREEZE_THIS -> 'can' 'i' 'freeze' 'this'
SAFE_TEMP_FOR -> 'safe' 'temp' 'for'
IS_PHRASE_SAFE -> 'is' PHRASE 'safe'
CAN_I_MAKE_THIS_AHEAD -> 'can' 'i' 'make' 'this' 'ahead'
MARINATE_OVERNIGHT -> 'marinate' 'overnight'
WHAT_CAN_I_USE_INSTEAD_OF -> 'what' 'can' 'i' 'use' 'instead' 'of'
SUB_FOR -> 'sub' 'for'
I_DONT_HAVE -> 'i' "don't" 'have'
WHAT_SIZE -> 'what' 'size'
WHAT_IS_A -> 'what' 'is' 'a'
HOWTO_VAGUE -> 'how' 'do' 'i' 'do' 'that'
"""


# Build the parser once
_cfg = CFG.fromstring(GRAMMAR)
_parser = EarleyChartParser(_cfg)


# --------------------------
# 2) Regex fallback (more robust coverage)
# --------------------------
REGEX_PATTERNS: Dict[str, re.Pattern] = {
    "ASK_HOWTO_SPECIFIC": re.compile(r"^\s*how\s+to\s+.+", re.I),
    "ASK_WHAT_IS": re.compile(r"^\s*what\s+is\s+.+", re.I),
    "ASK_SUB": re.compile(r"(instead of|sub\s+for)\s+.+", re.I),
    "ASK_MISSING": re.compile(r"i\s+don'?t\s+have\s+.+", re.I),
    "ASK_DIET": re.compile(r"(gluten[- ]free|dairy[- ]free|vegan|vegetarian).*(sub|alt|alternative|option)|substitute\s+for\s+.+", re.I),
    "ASK_AHEAD": re.compile(r"(make.*ahead|marinate.*overnight)", re.I),
    "ASK_STORAGE": re.compile(r"(freeze\s+this|how\s+long.*keep)", re.I),
    "ASK_TROUBLE": re.compile(r"(too\s+\w+|burning|not\s+melting|edges\s+burning|sauce\s+too\s+\w+)", re.I),
    "ASK_SAFETY": re.compile(r"(safe\s+temp|is\s+.+\s+safe)", re.I),
    "ASK_CONVERT": re.compile(r"\b(grams?|ml|milliliters?|liters?|cups?|tablespoons?|teaspoons?|oz|ounces?)\b.*\b(to|in)\b.*\b(grams?|ml|milliliters?|liters?|cups?|tablespoons?|teaspoons?|oz|ounces?)\b", re.I),
    "ASK_TOOL": re.compile(r"^\s*what\s+is\s+a\s+.+", re.I),
    "ASK_TOOL_SUB": re.compile(r"^\s*no\s+\w+.*(what\s+can\s+i\s+use|instead)", re.I),
    "ASK_SIZE": re.compile(r"(what\s+size\s+\w+|^\s*(8x8|9x9|9x13|12-inch|10-inch|11x7)\s+ok\??)", re.I),
    "ASK_HOWTO_VAGUE": re.compile(r"^\s*how\s+(do|should)\s+i\s+(do\s+that|do\s+it)\??\s*$", re.I),
}


EXTERNAL_LOOKUP_INTENTS = set(REGEX_PATTERNS.keys())


# --------------------------
# 3) Tokenization helper for CFG
# --------------------------
def simple_tokenize(s: str):
    """
    Very lightweight tokenizer:
    - lowercase
    - keep simple tokens, split on whitespace and punctuation (except x in sizes, hyphens, digits)
    """
    s = s.strip().lower()
    # keep tokens like 9x13, 12-inch, degrees symbol may appear
    # replace question marks with space
    s = re.sub(r"[?\.,!;:]+", " ", s)
    # collapse whitespace
    s = re.sub(r"\s+", " ", s)
    return s.split()


# --------------------------
# 4) Classification using CFG then regex fallback
# --------------------------
def classify_external_lookup(user_text: str) -> Tuple[bool, Optional[str]]:
    """
    Returns (needs_search, intent_name_if_known)
    Tries CFG first; if parsing succeeds to any top-level S alternative, we mark as search.
    Otherwise uses regex patterns.
    """
    tokens = simple_tokenize(user_text)
    try:
        # Try to parse; if at least one complete parse exists, accept as external.
        # We'll attempt a small cap to avoid heavy work on long inputs.
        parses = _parser.parse(tokens)
        for _ in parses:
            return True, "CFG_MATCH"
    except Exception:
        pass

    # Regex fallback
    for intent, pat in REGEX_PATTERNS.items():
        if pat.search(user_text):
            return True, intent

    return False, None


# --------------------------
# 5) Query builder and link generator
# --------------------------
def build_query(user_text: str) -> str:
    """
    Build a search query string. Minimal processing:
    - collapse spaces
    - don't over-normalize; user question often is a good query
    """
    q = re.sub(r"\s+", " ", user_text.strip())
    return urllib.parse.quote_plus(q)


def build_links(query: str) -> Dict[str, str]:
    return {
        "google": f"https://www.google.com/search?q={query}",
        "youtube": f"https://www.youtube.com/results?search_query={query}",
    }


# --------------------------
# 6) Public API
# --------------------------
def route_question(user_text: str) -> Dict[str, str]:
    """
    Determine whether the question requires external search.
    If yes, return links. If not, declare it's recipe-grounded.
    Returns a dict with keys:
      - 'route': 'search' | 'recipe'
      - 'intent': str | None
      - 'google': url (if search)
      - 'youtube': url (if search)
    """
    is_search, intent = classify_external_lookup(user_text)
    if is_search:
        q = build_query(user_text)
        links = build_links(q)
        return {"route": "search", "intent": intent, **links}
    return {"route": "recipe", "intent": None}


# --------------------------
# 7) CLI for quick manual testing
# --------------------------
def main():
    print("Type a question (Ctrl+C to exit).")
    while True:
        try:
            line = input("> ").strip()
            if not line:
                continue
            result = route_question(line)
            if result["route"] == "search":
                print("[SEARCH] google:", result["google"])
                print("         youtube:", result["youtube"])
            else:
                print("[RECIPE] handle this from the parsed recipe.")
        except (KeyboardInterrupt, EOFError):
            print("\nbye!")
            break


if __name__ == "__main__":
    main()

