# hybrid/extractor.py

"""
Hybrid extractor: fetch HTML and parse recipe using the LLM-based parser.
"""

from typing import Dict, Any

from fetch import fetch_html
from hybrid.model_wrappers import parse_recipe_from_html


def load_recipe_from_url(url: str) -> Dict[str, Any]:
    """
    Fetch the recipe HTML from the given URL and parse it with the LLM.

    Returns a dict with:
      - title
      - ingredients (list of strings)
      - steps (list of strings)
      - servings
      - prep_time
      - cook_time
      - total_time
    """
    html = fetch_html(url)
    recipe = parse_recipe_from_html(html)
    return recipe
