# llm_client.py

import os
from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors  # <-- add this

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError(
        "GEMINI_API_KEY not found. Please create a .env file with "
        "GEMINI_API_KEY=your_api_key_here"
    )

client = genai.Client(api_key=API_KEY)

DEFAULT_MODEL = "gemini-2.5-flash-lite"
DEFAULT_TEMPERATURE = 0.4
DEFAULT_MAX_TOKENS = 512


def ask_gemini(
    prompt: str,
    model: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    max_output_tokens: int = DEFAULT_MAX_TOKENS,
) -> str:
    """
    Send a plain-text prompt to Gemini and return the response text.

    Wraps common API errors (like quota exhaustion) in a RuntimeError so
    callers can handle them gracefully.
    """
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config={
                "temperature": temperature,
                "max_output_tokens": max_output_tokens,
            },
        )
    except genai_errors.ClientError as e:
        # Typical case: 429 RESOURCE_EXHAUSTED (quota / rate limit)
        raise RuntimeError(f"Gemini API error: {e}") from e

    return response.text.strip()
