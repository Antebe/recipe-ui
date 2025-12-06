# hybrid/model_wrappers.py

"""
Wrapper functions around the Gemini client and prompt builders.

- parse_recipe_from_html(html)  -> dict
- classify_intent(user_message) -> str label
- answer_with_context(...)      -> str answer
"""

import json
import re
from typing import Dict, Any, List, Tuple

from llm_client import ask_gemini
from prompts.parser_prompt import build_parser_prompt
from prompts.intent_prompt import build_intent_prompt
from prompts.qa_prompt import build_qa_prompt
from hybrid.state import RecipeState

def parse_recipe_from_html(html: str) -> Dict[str, Any]:
    """
    Use the LLM parser prompt to turn raw HTML into a structured recipe dict.
    Handles cases where the LLM wraps JSON in markdown code fences.
    """
    prompt = build_parser_prompt(html)
    raw = ask_gemini(prompt).strip()

    # 1) Try direct JSON first
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # 2) If that fails, try to extract JSON between braces (handles ```json fences)
        match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if not match:
            raise ValueError(
                "LLM did not return valid JSON and no JSON block could be found.\n\n"
                f"Raw output:\n{raw}"
            )
        raw_json = match.group(0)
        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"LLM did not return valid JSON: {e}\n\nExtracted block:\n{raw_json}"
            )

    # Basic sanity checks; you can add more if you want.
    data.setdefault("title", "Unknown title")
    data.setdefault("ingredients", [])
    data.setdefault("steps", [])
    data.setdefault("servings", None)
    data.setdefault("prep_time", None)
    data.setdefault("cook_time", None)
    data.setdefault("total_time", None)

    return data


def classify_intent(user_message: str) -> str:
    """
    Ask the LLM to classify the user message into one of our intent labels.
    """
    prompt = build_intent_prompt(user_message)
    label = ask_gemini(prompt)
    return label.strip().upper()


def answer_with_context(
    user_message: str,
    recipe_state: RecipeState,
    recipe_data: Dict[str, Any],
    conversation_history: List[Tuple[str, str]],
) -> str:
    """
    Use the QA prompt with recipe data + current step + history.
    """
    step_context = recipe_state.build_step_context()
    prompt = build_qa_prompt(
        user_message=user_message,
        recipe_state=step_context,
        recipe_data=recipe_data,
        conversation_history=conversation_history,
    )
    answer = ask_gemini(prompt)
    return answer.strip()

def refine_howto_query(user_message: str) -> str:
    """
    Use the LLM to turn a messy user question into a clean 'how to' search query
    for YouTube.

    Example:
        "uhh how do I preheat this oven thing?" -> "how to preheat an oven"
    """
    prompt = f"""
You are helping prepare a YouTube search query.

Rewrite the following user message as a short, clear "how to" query someone
would type into YouTube. Keep only the essential action, no extra words.

User message: "{user_message}"

Return ONLY the cleaned search query text, with no quotes and no explanation.
"""
    query = ask_gemini(prompt)
    return query.strip()
