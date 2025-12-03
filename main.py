#main.py
from utils import *
from query_internally import *
from search_router import *
from llm_client import ask_gemini
from extract import extract_recipe

def build_system_prompt(recipe_text: str) -> str:
    return f"""
You are a COOKING ASSISTANT. Stay only in the recipe text. You help users understand steps, ingredients, quantities and you guide them through the recipe conversationally.
Do not make up ingredients or steps that are not in the html. You can explain how to perform cooking actions.You can summarize steps, ingredients, or guide the user. 

Here is the recipe context:

{recipe_text}

Wait for the next user question and answer based only on this recipe.
"""


def main():
    print("=== LLM-Only Recipe Assistant ===")
    print("Type 'exit' to quit.\n")

    system_prompt = ""
    recipe_loaded = False

    while True:
        user_input = input("User: ").strip()

        if user_input.lower() in ["exit", "quit"]:
            print("Bot: Goodbye!")
            break

        # Load recipe
        if user_input.startswith("load "):
            url = user_input.replace("load", "").strip()
            print("Bot: Loading recipe...")

            recipe = extract_recipe(url)
            system_prompt = build_system_prompt(recipe)
            recipe_loaded = True

            print("Bot: Recipe loaded. Ask me anything!")
            continue

        if not recipe_loaded:
            print("Bot: Please load a recipe first using: load <URL>")
            continue

        # Build full LLM prompt
        full_prompt = (
            system_prompt
            + "\n\nUSER QUESTION:\n"
            + user_input
            + "\n\nASSISTANT ANSWER:\n"
        )

        bot_reply = ask_gemini(full_prompt)
        print("Bot:", bot_reply)



if __name__ == "__main__":
    main()

