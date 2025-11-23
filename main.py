from utils import *
from query_internally import *
from search_router import *

def main():
    state = None    # no recipe loaded yet

    print("=== Recipe Chat CLI ===")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("User: ").strip()

        # exit
        if user_input in ["exit", "quit"]:
            print("Bot: Goodbye!")
            break

        # LOAD RECIPE
        if user_input.startswith("load "):
            url = user_input.replace("load", "").strip()
            recipe = url_to_recipe(url)
            state = RecipeState(recipe)
            print("Bot: Loaded recipe.")
            continue

        # must load a recipe first
        if state is None:
            print("Bot: Please load a recipe first using: load <URL>")
            continue

        # NAVIGATION FIRST
        nav_answer, new_step = answer_navigation_question(user_input, state)
        if nav_answer != "I can’t tell how to navigate from that.":
            print("Bot:", nav_answer)
            continue

        # ROUTE QUESTION (search vs internal)
        routed = route_question(user_input)
        if routed["route"] == "search":
            print("Bot: External lookup needed.")
            print("Google:", routed["google"])
            print("YouTube:", routed["youtube"])
            continue

        # INTERNAL RECIPE QUESTION
        print("Bot:", answer_recipe_question(user_input, state.recipe, state.current_step))


if __name__ == "__main__":
    # R = url_to_recipe("https://www.allrecipes.com/recipe/219077/chef-johns-perfect-mashed-potatoes/")
    # print(R.ingredients)
    main()
