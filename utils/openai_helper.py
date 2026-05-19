"""
OpenAI helper.

Centralizes API key loading and OpenAI chat calls.
"""

import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


def get_client() -> OpenAI:
    """Create an OpenAI client using the API key from environment variables."""
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY is not set. Add it to your .env file or Streamlit secrets."
        )

    return OpenAI(
        api_key=api_key,
        timeout=30.0,
        max_retries=2,
    )


def chat_completion(
    system_prompt: str,
    user_message: str,
    model: str = "gpt-4o-mini",
) -> str:
    """Send a single chat request and return the assistant response."""
    client = get_client()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
        max_tokens=1024,
    )

    content = response.choices[0].message.content

    if not content:
        return ""

    return content.strip()