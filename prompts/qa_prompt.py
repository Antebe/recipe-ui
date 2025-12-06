# prompts/qa_prompt.py

"""
Prompt template for contextual question answering in the hybrid system.

We provide:
- structured recipe data (title, ingredients, steps, times, etc.)
- current step state (step number, description, ingredients, tools, etc.)
- short conversation history
- the latest user question

The LLM should answer concisely, grounded in the recipe when possible.
"""


def build_qa_prompt(
    user_message: str,
    recipe_state: dict,
    recipe_data: dict,
    conversation_history: list[tuple[str, str]],
) -> str:
    """
    conversation_history: list of (speaker, text) pairs, e.g. [("User", "..."), ("Assistant", "...")]
    recipe_state: e.g. {
        "current_step": 3,
        "description": "...",
        "ingredients": [...],
        "tools": [...],
        "methods": [...],
        "time": {...},
        "temperature": {...}
    }
    recipe_data: the parsed recipe dict from the parser (title, ingredients, steps, times, etc.)
    """
    history_lines = [f"{speaker}: {text}" for speaker, text in conversation_history]
    history_text = "\n".join(history_lines)

    return f"""
You are a careful and concise cooking assistant.

You are helping the user follow this recipe and answer questions about it.

---------------- RECIPE DATA ----------------
{recipe_data}

---------------- CURRENT STEP STATE ----------------
{recipe_state}

---------------- CONVERSATION HISTORY ----------------
{history_text}

---------------- USER QUESTION ----------------
{user_message}

Instructions:
- Answer based on the recipe data and the current step whenever possible.
- If the recipe does not explicitly say something, you may use general cooking knowledge,
  but clearly mark it as a suggestion (e.g., "The recipe does not say, but usually ...").
- If you truly do not know, say you are not sure instead of making things up.
- Be brief and to the point. Use plain text suitable for a terminal chat.
"""
