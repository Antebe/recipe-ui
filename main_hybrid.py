# main_hybrid.py
"""
Part 3 — Hybrid System entrypoint.

This script:
- Asks the user for a recipe URL.
- Fetches the HTML (fetch.py).
- Uses the LLM-based parser to extract a recipe (hybrid/extractor.py).
- Tracks the current step in Python (hybrid/state.py).
- Classifies user intents with an LLM (hybrid/model_wrappers.py).
- Answers questions with LLM using structured context.
- Calls a YouTube search tool for "how to" questions.
"""

import re
from typing import Optional

from hybrid.model_wrappers import answer_with_context
from hybrid.extractor import load_recipe_from_url
from hybrid.state import RecipeState
from hybrid.history import ConversationHistory
from hybrid.youtube import youtube_search
from hybrid.model_wrappers import (
    classify_intent,
    answer_with_context,
    refine_howto_query,
)


def show_recipe_overview(recipe: dict) -> None:
    """Print a brief overview of the recipe."""
    title = recipe.get("title", "Unknown title")
    servings = recipe.get("servings") or "Unknown"
    prep_time = recipe.get("prep_time") or "Unknown"
    cook_time = recipe.get("cook_time") or "Unknown"
    total_time = recipe.get("total_time") or "Unknown"

    print(f"\n=== {title} ===")
    print(f"Servings: {servings}")
    print("Times:")
    print(f"  Prep:  {prep_time}")
    print(f"  Cook:  {cook_time}")
    print(f"  Total: {total_time}\n")


def show_ingredients(recipe: dict) -> None:
    print("\nIngredients:")
    for line in recipe.get("ingredients", []):
        print(f"- {line}")
    print("")


def show_all_steps(recipe: dict) -> None:
    print("\nSteps:")
    for i, step in enumerate(recipe.get("steps", []), start=1):
        print(f"{i}. {step}")
    print("")


def interpret_navigation(user_message: str, state: RecipeState) -> None:
    """
    Rule-based navigation using Python, while the LLM only gives us the intent
    label STEP_NAVIGATION.

    Heuristics:
    - "first", "start", "begin" -> first step
    - "back", "previous"        -> previous step
    - "step N"                  -> go to that step
    - otherwise                 -> next step
    """
    text = user_message.lower()

    # Explicit "step N"
    match = re.search(r"step\s+(\d+)", text)
    if match:
        idx = int(match.group(1)) - 1
        state.go_to_step(idx)
        return

    if any(word in text for word in ["first", "start", "begin"]):
        state.go_to_first()
    elif "back" in text or "previous" in text:
        state.prev_step()
    else:
        # default: go forward
        if state.current_step is None:
            state.go_to_first()
        else:
            state.next_step()


def show_current_step_with_parse(
    state: RecipeState,
    recipe: dict,
    history: ConversationHistory,
) -> None:
    """
    Show the current step AND ask the LLM to provide a deeper parse automatically.
    """
    if not state.has_steps():
        print("Bot: This recipe does not seem to have any steps.")
        return

    if state.current_step is None:
        state.go_to_first()

    step_num = state.current_step + 1
    total = state.total_steps()
    text = state.get_current_step_text() or "(no text for this step)"

    # 1) Print the raw step text
    step_line = f"Step {step_num} of {total}: {text}"
    print("Bot:", step_line)
    history.add_bot(step_line)

    # 2) Ask the LLM for a deeper parse of the current step
    user_msg = (
        "Please provide a deeper parse of the current step. "
        "List the main actions, ingredients, methods, tools, time, and temperature "
        "in a clear, structured bullet format."
    )

    # We use the same QA function, but with a fixed question
    try:
        answer = answer_with_context(
            user_message=user_msg,
            recipe_state=state,
            recipe_data=recipe,
            conversation_history=history.as_list(),
        )
        print("Bot:", answer)
        history.add_bot(answer)
    except Exception as e:
        # If the LLM call fails (e.g., quota), we still at least show the step text
        print("Bot: (Could not generate deeper parse for this step.)")
        print("Bot: Error:", e)
        history.add_bot("(Could not generate deeper parse for this step.)")



def detect_simple_intent(user_msg: str) -> Optional[str]:
    """
    Lightweight, rule-based shortcut for very common commands.
    This avoids calling the LLM for simple things like 'ingredients', 'steps',
    'next', 'back', etc., even if the user also says 'hi' or adds extra words.
    """
    text = user_msg.strip().lower()

    # If they mention ingredients anywhere, treat as RECIPE_OVERVIEW
    # Examples: "ingredients", "ingredients list", "show all ingredients",
    # "hi, can you show ingredients", etc.
    if "ingredient" in text:
        return "RECIPE_OVERVIEW"

    # Very common navigation patterns
    if any(kw in text for kw in ["next", "next step", "what's next", "whats next"]):
        return "STEP_NAVIGATION"

    if any(kw in text for kw in ["back", "previous", "prev", "go back"]):
        return "STEP_NAVIGATION"

    if any(kw in text for kw in ["repeat", "again", "say that again", "what was that"]):
        return "STEP_REPEAT"

    # If they mention "step X", we still treat it as navigation
    if "step" in text:
        return "STEP_NAVIGATION"

    # No simple rule-based mapping found
    return None



def main() -> None:
    print("=== Hybrid Recipe Chat (Part 3) ===")
    print("Type 'exit' to quit.\n")

    # 1) Ask for recipe URL and load via hybrid extractor (LLM-based parser)
    url = input("Please paste a recipe URL (e.g., from allrecipes.com):\n> ").strip()
    if not url:
        print("No URL provided. Exiting.")
        return

    print("\nLoading and parsing recipe with LLM...")
    try:
        recipe = load_recipe_from_url(url)
    except Exception as e:
        print("Error while loading/parsing the recipe:")
        print(e)
        return

    # 2) Initialize state + history
    state = RecipeState(recipe=recipe)
    history = ConversationHistory()

    show_recipe_overview(recipe)
    state.go_to_first()
    show_current_step_with_parse(state, recipe, history)


    print("\nYou can now ask questions about this recipe.")
    print("Examples:")
    print("- 'Show me the ingredients list.'")
    print("- 'What is the next step?'")
    print("- 'How much salt do I need?'")
    print("- 'How do I preheat the oven?'")
    print("- 'Repeat that step.'\n")

    # 3) Conversation loop
    while True:
        user_msg = input("User: ").strip()
        if user_msg.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        if not user_msg:
            continue

        history.add_user(user_msg)

        # Lightweight rule-based shortcut first
        simple_intent = detect_simple_intent(user_msg)
        if simple_intent is not None:
            intent = simple_intent
        else:
            intent = classify_intent(user_msg)


        # Route based on intent
        if intent == "STEP_NAVIGATION":
            interpret_navigation(user_msg, state)
            show_current_step_with_parse(state, recipe, history)


        elif intent == "STEP_REPEAT":
            # Just show the current step again; if none, go to first
            if state.current_step is None:
                state.go_to_first()
            show_current_step_with_parse(state, recipe, history)


        elif intent == "RECIPE_OVERVIEW":
            # Decide whether they want ingredients vs steps vs both
            text = user_msg.lower()
            if "ingredient" in text:
                show_ingredients(recipe)
            elif "step" in text or "direction" in text:
                show_all_steps(recipe)
            else:
                show_recipe_overview(recipe)

        elif intent == "HOW_TO":
            # 1) Let LLM answer in text with context
            answer = answer_with_context(
                user_message=user_msg,
                recipe_state=state,
                recipe_data=recipe,
                conversation_history=history.as_list(),
            )
            print("Bot:", answer)
            history.add_bot(answer)

            # 2) Also provide a YouTube link using a refined query
            try:
                query = refine_howto_query(user_msg)
            except Exception:
                # Fallback: use raw user message if refinement fails
                query = user_msg
            link = youtube_search(query)
            extra = f"If you prefer a video, you can search: {link}"
            print("Bot:", extra)
            history.add_bot(extra)

        else:
            # For all other intents (INGREDIENT_QUERY, TIME_QUERY, etc.),
            # delegate to the LLM QA with structured context.
            answer = answer_with_context(
                user_message=user_msg,
                recipe_state=state,
                recipe_data=recipe,
                conversation_history=history.as_list(),
            )
            print("Bot:", answer)
            history.add_bot(answer)


if __name__ == "__main__":
    main()
