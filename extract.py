# extract.py
import json
from bs4 import BeautifulSoup
from fetch import fetch_html


def extract_json_ld(html: str):
    # Find and return the JSON-LD recipe object inside the HTML.
    # Returns a dict with recipe fields OR None if not found.

    # include beautiful soup in readme
    soup = BeautifulSoup(html, "lxml")

    scripts = soup.find_all("script", {"type": "application/ld+json"})
    if not scripts:
        return None

    for script in scripts:
        raw = script.string or script.text
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue

        # JSON-LD can be a list OR a single dict
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and is_recipe(item):
                    return extract_fields(item)

        elif isinstance(data, dict) and is_recipe(data):
            return extract_fields(data)

    return None


def is_recipe(obj: dict) -> bool:
    # Return True if the JSON-LD object represents a recipe.
    t = obj.get("@type")
    if t == "Recipe":
        return True
    if isinstance(t, list) and "Recipe" in t:
        return True
    return False


def extract_fields(ld_obj: dict):
    title = ld_obj.get("name", "Untitled Recipe")
    ingredients = ld_obj.get("recipeIngredient", [])

    # JSON-LD instructions (as before)
    raw = ld_obj.get("recipeInstructions", [])
    steps = []

    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict):
                txt = item.get("text", "").strip()
                if txt:
                    steps.append(txt)
            elif isinstance(item, str) and item.strip():
                steps.append(item.strip())
    else:
        if isinstance(raw, str) and raw.strip():
            steps = [raw.strip()]

    # NEW — Extract metadata
    servings = ld_obj.get("recipeYield")
    total_time = ld_obj.get("totalTime")
    prep_time = ld_obj.get("prepTime")
    cook_time = ld_obj.get("cookTime")

    return {
        "title": title,
        "ingredients": ingredients,
        "steps": steps,
        "servings": servings,
        "total_time": total_time,
        "prep_time": prep_time,
        "cook_time": cook_time
    }




def extract_recipe(url: str):
    """
    High-level function:
      1. Fetch HTML
      2. Extract JSON-LD
      3. Return recipe dict or raise error
    """
    html = fetch_html(url)
    data = extract_json_ld(html)

    if data is None:
        raise ValueError("No JSON-LD recipe data found.")
    return data


if __name__ == "__main__":
    url = input("Enter AllRecipes URL: ").strip()
    recipe = extract_recipe(url)
    fields = extract_fields(recipe)

    print(fields)
    print("\nTITLE:", recipe["title"])
    print("\nINGREDIENTS:")
    for ing in recipe["ingredients"]:
        print(" -", ing)

    print("\nSTEPS:")
    for i, step in enumerate(recipe["steps"], 1):
        print(f"{i}. {step}")
