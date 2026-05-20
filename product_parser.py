"""
product_parser.py
-----------------
Extracts structured product data (name, price, category) from raw unstructured
text using the OpenAI API.
"""

import json
import os
import time
import logging
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI, APIError, RateLimitError, APIConnectionError

# ── Setup ─────────────────────────────────────────────────────────────────────

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

MODEL = "gpt-3.5-turbo"
MAX_RETRIES = 3
BACKOFF_BASE = 2

# ── Tool Schema ───────────────────────────────────────────────────────────────

PRODUCT_TOOL = {
    "type": "function",
    "function": {
        "name": "extract_product",
        "description": (
            "Extract structured product information from raw text. "
            "If price is not mentioned or cannot be determined, set it to null."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The product name, as specific as possible.",
                },
                "price": {
                    "type": ["number", "null"],
                    "description": "Numeric price as a float. null if not found.",
                },
                "category": {
                    "type": "string",
                    "description": "Product category e.g. Electronics, Footwear.",
                },
            },
            "required": ["name", "price", "category"],
        },
    },
}

# ── Validation ────────────────────────────────────────────────────────────────

def validate_product(data: dict) -> dict:
    """
    Validate and clean the extracted product dictionary.
    """
    name = data.get("name", "").strip()
    if not name:
        raise ValueError("Validation failed: 'name' is empty or missing.")

    price = data.get("price")
    if price is not None:
        try:
            price = float(price)
        except (TypeError, ValueError):
            raise ValueError(f"Validation failed: 'price' is not numeric: {price!r}")
        if price <= 0:
            raise ValueError(f"Validation failed: 'price' must be positive, got {price}")

    category = data.get("category", "").strip()
    if not category:
        raise ValueError("Validation failed: 'category' is empty or missing.")

    return {"name": name, "price": price, "category": category}

# ── Retry Helper ──────────────────────────────────────────────────────────────

def call_with_retry(fn, *args, **kwargs):
    """
    Call fn with exponential backoff on transient API errors.
    """
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return fn(*args, **kwargs)
        except (RateLimitError, APIConnectionError, APIError) as exc:
            wait = BACKOFF_BASE ** attempt
            logger.warning(
                "API error on attempt %d/%d – retrying in %ds. Error: %s",
                attempt, MAX_RETRIES, wait, exc,
            )
            last_error = exc
            time.sleep(wait)
    raise last_error

# ── Approach 1: Function Calling ──────────────────────────────────────────────

def parse_with_function_calling(text: str) -> dict:
    """
    Extract product data using OpenAI function calling.
    Forces the model to always return structured output.
    """
    def _call():
        return client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a product data extraction assistant. "
                        "Extract the product name, price as a plain number, "
                        "and category from the user's text. "
                        "If the price is missing, set it to null."
                    ),
                },
                {"role": "user", "content": text},
            ],
            tools=[PRODUCT_TOOL],
            tool_choice={"type": "function", "function": {"name": "extract_product"}},
        )

    response = call_with_retry(_call)

    tool_calls = response.choices[0].message.tool_calls
    if not tool_calls:
        raise ValueError("No tool call returned by the model.")

    raw_args = tool_calls[0].function.arguments
    try:
        data = json.loads(raw_args)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Could not parse tool arguments as JSON: {exc}") from exc

    return validate_product(data)

# ── Approach 2: JSON Mode ─────────────────────────────────────────────────────

def parse_with_json_mode(text: str) -> dict:
    """
    Extract product data using OpenAI JSON mode.
    Relies on prompt instructions for structure.
    """
    def _call():
        return client.chat.completions.create(
            model=MODEL,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a product data extraction assistant. "
                        'Return ONLY a JSON object with keys "name" (string), '
                        '"price" (number or null), and "category" (string). '
                        "If the price is not mentioned, set it to null. "
                        "Do not include any explanation outside the JSON."
                    ),
                },
                {"role": "user", "content": text},
            ],
        )

    response = call_with_retry(_call)

    raw_content = response.choices[0].message.content
    try:
        data = json.loads(raw_content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Could not parse JSON mode response: {exc}") from exc

    return validate_product(data)

# ── Main ──────────────────────────────────────────────────────────────────────

def parse_product(text: str, approach: str = "function_calling") -> Optional[dict]:
    """
    Main entry point. Parse a product description with the chosen approach.
    """
    logger.info("Parsing: %s", text[:80])
    try:
        if approach == "function_calling":
            result = parse_with_function_calling(text)
        elif approach == "json_mode":
            result = parse_with_json_mode(text)
        else:
            raise ValueError(f"Unknown approach: {approach!r}")
        logger.info("Result: %s", result)
        return result
    except (ValueError, KeyError) as exc:
        logger.error("Parsing failed: %s", exc)
        return None


if __name__ == "__main__":
    sample = "Nike Air Max 90 – great for running, just ₹4,500 only!"
    print(parse_product(sample))