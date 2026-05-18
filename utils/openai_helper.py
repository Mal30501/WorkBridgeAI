"""
utils/openai_helper.py

Centralised wrapper around the OpenAI client.
Keeps API key loading and basic error handling in one place.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def get_client() -> OpenAI:
    """Return an authenticated OpenAI client, raising early if key is missing."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY is not set. "
            "Copy .env.example to .env and add your key."
        )
    return OpenAI(api_key=api_key)


def chat_completion(system_prompt: str, user_message: str, model: str = "gpt-4o-mini") -> str:
    """
    Send a single-turn chat completion request.

    Args:
        system_prompt: Instructions that shape the model's behaviour.
        user_message:  The actual content to process.
        model:         OpenAI model name (default gpt-4o-mini for cost efficiency).

    Returns:
        The assistant's reply as a plain string.

    Raises:
        EnvironmentError: if the API key is missing.
        Exception: re-raised from the OpenAI SDK for the caller to handle.
    """
    client = get_client()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
        temperature=0.2,   # Low temperature keeps answers grounded and consistent
        max_tokens=1024,
    )
    return response.choices[0].message.content.strip()
