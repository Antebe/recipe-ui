#https://www.allrecipes.com/recipe/8934/garlic-chicken-stir-fry/
from extract import extract_recipe
from utils import *
from steps_parsing import *

recipe_url = "https://www.allrecipes.com/recipe/8934/garlic-chicken-stir-fry/"
recipe = extract_recipe(recipe_url)
atomic = get_atomic_sentences(recipe)
print("\nATOMIC SENTENCES:")
for i, s in enumerate(atomic, 1):
    print(f"{i}: {s}")

matches = get_ingredients_by_step(recipe)

print(collect_all_ingredients(matches))
