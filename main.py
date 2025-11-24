#main.py
from utils import *
from query_internally import *
from search_router import *



def main():
    print("=== Recipe Chat CLI ===")
    print("Type 'exit' to quit.\n")

    state = None

    while True:
        user_input = input("User: ").strip()

        # Exit program
        if user_input.lower() in ["exit", "quit"]:
            print("Bot: Goodbye!")
            break

        # LOAD A RECIPE
        if user_input.startswith("load "):
            url = user_input.replace("load", "").strip()

            print("Bot: Loading recipe...")
            recipe = url_to_recipe(url)
            state = RecipeState(recipe)

            print(f"Bot: Loaded recipe -> \"{recipe.title}\".")
            print("Bot: What would you like to do?")
            print("  [1] Show ingredients")
            print("  [2] Walk through steps")
            print("  [3] Show a recipe summary")
            continue

        # If no recipe yet
        if state is None:
            print("Bot: Please load a recipe first using: load <URL>")
            continue

        # MENU SELECTION (1, 2 or 3)
        if user_input == "1":
            print(f"Bot: Ingredients:\n")
            for ing in state.recipe.ingredients:
                print(" -", ing.raw)
            continue

        if user_input == "2":
            state.current_step = 1
            print(f"Bot: Step 1: {state.recipe.steps[0].text}")
            continue

        if user_input == "3":
            summary = state.recipe
            print("Bot: Recipe Summary:\n")
            for step in summary.steps:
                print(f" Step {step.step_number}: {step.text}")
            continue
        # STEP NAVIGATION (internal)
        nav_answer, new_step = answer_navigation_question(user_input, state)
        if nav_answer != "I can’t tell how to navigate from that.":
            print("Bot:", nav_answer)
            continue

        # SEARCH ROUTING (external)
        routed = route_question(user_input)
        if routed["route"] == "search":
            print("Bot: I found external references for you:")
            print("  Google:", routed["google"])
            print("  YouTube:", routed["youtube"])
            continue

        # INTERNAL RECIPE QA
        answer = answer_recipe_question(
            user_input,
            state.recipe,
            state.current_step
        )
        print("Bot:", answer)

if __name__ == "__main__":
    main()
