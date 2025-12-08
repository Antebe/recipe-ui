#main.py
from pydoc import text
from utils import *
from query_internally import *
from search_router import *
from llm_client import ask_gemini
from extract import extract_recipe
from llm_step_navigation import *

def build_system_prompt(recipe_text: str) -> str:
    return f"""
Your role is to return recipe steps, ingredients, and answer questions of the user. You will scrape the HTML provided and extract steps, ingredients, and important rules. 
Separate the steps into atomic sentences to make clear singular steps for the user. Hold each step in a class. When prompted, return singular steps. 
Return ingredients when prompted. When prompted with questions outside of the recipe, guide the user to a youtube or google link for "how to" questions.


Here is the recipe context:

{recipe_text}

Wait for the next user question and answer based only on this recipe.
"""



def main():
    print("=== LLM-Only Recipe Assistant ===")
    print("Type 'exit' to quit.\n")

    system_prompt = ""
    recipe_loaded = False
    current_step = 0

    while True:
        user_input = input("User: ").strip()

        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Bot: Goodbye!")
            break

        # Load recipe
        if user_input.startswith("load "):
            url = user_input.replace("load", "").strip()
            print("Bot: Loading recipe...")

            recipe = extract_recipe(url)
            system_prompt = build_system_prompt(recipe['title'] +\
                                                "\n\nIngredients:\n" +\
                                                "\n".join(recipe['ingredients']) +\
                                                "\n\nSteps:\n" + "\n".join([f"{i+1}. {e}" for i, e in enumerate(recipe['steps'])]) +\
                                                "\n Total Steps: " + str(len(recipe['steps'])))
            recipe_loaded = True
            current_step = 0
            total_steps = len(recipe['steps'])
            print("Bot: Recipe loaded. Ask me anything!")
            continue

        if not recipe_loaded:
            print("Bot: Please load a recipe first using: load <URL>")
            continue

        ####### Routing logic #######
        result = route_question(user_input)
        if result["route"] == "search":
            print(f"[SEARCH] intent={result['intent']}")
            print("  Google :", result["google"])
            print("  YouTube:", result["youtube"])
            continue
        #############################

        #step navigation detection
        new_step = detect_step_navigation(user_input, current_step, total_steps)
        if new_step != current_step:
            current_step = new_step
            print(f"[STEP TRACKER] Moving to step {current_step}/{total_steps}")
        
        step_context = build_step_context(current_step, total_steps)
        
        # Build full LLM prompt
        full_prompt = (
            step_context +
            system_prompt
            + "\n\nUSER QUESTION:\n"
            + user_input
            + "\n\nASSISTANT ANSWER:\n"
        )

        print(full_prompt)
        bot_reply = ask_gemini(full_prompt)
        print("Bot:", bot_reply)

        system_prompt += f"\n\nUSER QUESTION:\n{user_input}\n\nASSISTANT ANSWER:\n{bot_reply}\n"



if __name__ == "__main__":
    main()

