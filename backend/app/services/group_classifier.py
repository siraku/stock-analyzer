"""
AI-powered thematic group classifier for portfolio positions.
Sends a single batch request to OpenRouter; each ticker gets a concise theme name
like "Cyber Security", "Space", "AI / Data Analytics", etc.
"""
import json

import httpx

from app.config import settings

_SYSTEM_PROMPT = (
    "You are a portfolio analyst specializing in thematic investment classification. "
    "Given a list of US stocks, assign each one to a concise thematic investment group. "
    "Use meaningful names such as: Cyber Security, Space, AI / Data Analytics, "
    "Cloud Infrastructure, Semiconductors, Defense & Aerospace, Consumer Tech, "
    "Healthcare, Fintech, Energy, Industrial, E-Commerce, Media & Entertainment. "
    "Create new theme names when needed — be specific and consistent: "
    "stocks with overlapping business focus should share the same theme name. "
    "Return ONLY a valid JSON object mapping ticker to theme: "
    '{"TICKER": "Theme Name", ...} — no markdown, no explanation.'
)


def classify_tickers(positions: list[dict]) -> dict[str, str]:
    """
    Classify a list of {ticker, company_name} position dicts into thematic groups.
    Returns {ticker: group_name}. Falls back to "Uncategorized" on any failure.
    """
    if not positions:
        return {}
    if not settings.openrouter_api_key:
        return {p["ticker"]: "Uncategorized" for p in positions}

    lines = "\n".join(f'{p["ticker"]} ({p["company_name"]})' for p in positions)
    user_prompt = f"Classify these stocks into thematic investment groups:\n{lines}"

    try:
        response = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.openrouter_model,
                "max_tokens": 1024,
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            },
            timeout=60.0,
        )
        response.raise_for_status()
        raw = response.json()["choices"][0]["message"]["content"].strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.rstrip("`").strip()

        result = json.loads(raw)
        # Ensure all input tickers have an entry
        return {p["ticker"]: result.get(p["ticker"], "Uncategorized") for p in positions}

    except Exception:
        return {p["ticker"]: "Uncategorized" for p in positions}
