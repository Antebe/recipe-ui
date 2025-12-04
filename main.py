#main.py
from utils import *
from query_internally import *
from search_router import *
from llm_client import ask_gemini
from extract import extract_recipe

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

        #print(full_prompt)
        bot_reply = ask_gemini(full_prompt)
        print("Bot:", bot_reply)

        system_prompt += f"\n\nUSER QUESTION:\n{user_input}\n\nASSISTANT ANSWER:\n{bot_reply}\n"



if __name__ == "__main__":
    main()

