# prompts/parser_prompt.py

"""
Prompt template for the LLM-based recipe parser.

We pass in the raw HTML of a recipe page and ask Gemini to extract:
- title
- ingredients (list of strings)
- steps (list of short, atomic steps as strings)
- servings
- prep_time
- cook_time
- total_time

The LLM must return VALID JSON only.
"""


def build_parser_prompt(html: str) -> str:
    return f"""
You are a recipe parser.

Your task:
- Read the HTML of a single recipe page.
- Extract the key recipe information.
- Return ONLY valid JSON, with this exact structure:

{{
  "title": str,
  "ingredients": [str, ...],
  "steps": [str, ...],
  "servings": str or null,
  "prep_time": str or null,
  "cook_time": str or null,
  "total_time": str or null
}}

Guidelines:
- "ingredients" should be the visible ingredient lines a human would read.
- "steps" should be short, mostly atomic cooking instructions in order.
- If some fields are not available, use null instead of inventing them.
- Do NOT include any explanation outside the JSON.
- Do NOT include comments or trailing commas.

Here is the raw HTML of the recipe page:

---------------- HTML START ----------------
{html}
---------------- HTML END ----------------
"""
