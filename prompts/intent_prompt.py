# prompts/intent_prompt.py

"""
Prompt template for intent classification.

We map each user message to EXACTLY ONE of the following labels:

INGREDIENT_QUERY   - asking about ingredients or quantities
STEP_NAVIGATION    - next, back, go to step X, repeat, what's next, etc.
STEP_REPEAT        - repeat / say that again / what was that
HOW_TO             - "how do I ..." questions (procedures/techniques)
DEFINITION         - "what is ..." questions (tools/terms)
SUBSTITUTE         - substitutions: instead of X / don't have X / can I use Y
TIME_QUERY         - how long, when is it done, timing questions
TEMPERATURE_QUERY  - oven temp, internal temp, temperature questions
RECIPE_OVERVIEW    - show ingredients, show recipe, show all steps
OTHER              - anything else (small talk, out-of-scope, etc.)
"""


def build_intent_prompt(user_message: str) -> str:
    return f"""
You are an intent classifier for a cooking assistant.

Classify the following user message into EXACTLY ONE of these labels:

- INGREDIENT_QUERY
- STEP_NAVIGATION
- STEP_REPEAT
- HOW_TO
- DEFINITION
- SUBSTITUTE
- TIME_QUERY
- TEMPERATURE_QUERY
- RECIPE_OVERVIEW
- OTHER

User message:
"{user_message}"

Rules:
- Return ONLY the label, in ALL CAPS, with no extra words.
- If the message is unclear or out of scope, return OTHER.
"""
