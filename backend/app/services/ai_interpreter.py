"""
OpenRouter API integration for interpreting technical indicator snapshots.
"""
import json
from typing import TYPE_CHECKING

import httpx

from app.config import settings
from app.services.indicators import SignalSnapshot
from app.services.scoring import get_signal_label

if TYPE_CHECKING:
    from app.services.fundamental_data import FundamentalSnapshot


_SYSTEM_PROMPT = """You are a financial analysis assistant for global equities. \
Your task is to assess whether a stock is showing credible trend reversal signals. \
You will be given technical indicator data and, when available, fundamental business context \
(revenue trend, margins, R&D spend, short interest, analyst sentiment, upcoming earnings). \
Use both to form your judgment — a reversal backed by improving fundamentals or a near-term catalyst \
is more credible than a purely technical signal on a deteriorating business.
Be concise, specific, and honest about uncertainty.
Always respond with valid JSON only — no markdown, no extra text."""


def build_prompt(snap: SignalSnapshot, score_value: int, fundamentals: "FundamentalSnapshot | None" = None) -> str:
    ema50_pct = None
    if snap.price_current and snap.ema50:
        ema50_pct = round((snap.price_current - snap.ema50) / snap.ema50 * 100, 1)

    prompt = f"""Stock: {snap.ticker}
Current price: {snap.price_current}
52-week range: {snap.price_52w_low} - {snap.price_52w_high}

TECHNICAL INDICATOR SNAPSHOT:
- RSI(14): {snap.rsi_14} [oversold threshold: 30]
- RSI bullish divergence detected: {snap.rsi_divergence}
- MACD value: {snap.macd_value}, Signal: {snap.macd_signal}, Histogram: {snap.macd_histogram}
- MACD bullish crossover (last 3 candles): {snap.macd_crossover}
- EMA20: {snap.ema20}, EMA50: {snap.ema50}
- Price vs EMA50: {ema50_pct}%
- Bollinger Bands: Upper {snap.bb_upper}, Middle {snap.bb_middle}, Lower {snap.bb_lower}
- Bollinger bounce (price back above lower band): {snap.bb_bounce}
- Volume ratio vs 20d avg: {snap.volume_ratio}x
- Stochastic %K: {snap.stoch_k}, %D: {snap.stoch_d}
- Stochastic bullish crossover in oversold zone: {snap.stoch_crossover}
- Candlestick pattern detected: {snap.candle_pattern or "none"}
- Pre-score: {score_value}/150
"""

    if fundamentals is not None:
        from app.services.fundamental_data import format_for_prompt
        prompt += "\n" + format_for_prompt(fundamentals) + "\n"

    prompt += """
Respond with this exact JSON structure:
{
  "reversal_likelihood": "high|medium|low|none",
  "confidence": <integer 0-100>,
  "key_signals": ["<signal 1>", "<signal 2>"],
  "risk_factors": ["<risk 1>", "<risk 2>"],
  "summary": "<2-3 sentence analysis in English>"
}"""
    return prompt


def interpret(snap: SignalSnapshot, score_value: int, fundamentals: "FundamentalSnapshot | None" = None) -> dict:
    """
    Call OpenRouter API and return parsed analysis dict.
    Falls back to a score-based result if the API call fails.
    """
    if not settings.openrouter_api_key:
        return _fallback_result(snap, score_value)

    try:
        response = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.openrouter_model,
                "max_tokens": 512,
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": build_prompt(snap, score_value, fundamentals)},
                ],
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        raw = data["choices"][0]["message"]["content"].strip()
        # Strip markdown code fences if present (e.g. ```json ... ```)
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1]  # drop opening ```[json]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.rstrip("`").strip()
        result = json.loads(raw)
        usage = data.get("usage", {})
        result["tokens_used"] = usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)
        return result
    except json.JSONDecodeError:
        return _fallback_result(snap, score_value)
    except Exception:
        return _fallback_result(snap, score_value)


def _fallback_result(snap: SignalSnapshot, score_value: int) -> dict:
    """Return a basic result derived from scoring when AI is unavailable."""
    label = get_signal_label(score_value)
    return {
        "reversal_likelihood": label,
        "confidence": min(score_value, 100),
        "key_signals": _derive_key_signals(snap),
        "risk_factors": ["AI analysis unavailable — result based on indicator scoring only"],
        "summary": f"Score-based assessment: {score_value}/150. "
                   f"Reversal likelihood: {label}. Configure OpenRouter API key for detailed analysis.",
        "tokens_used": 0,
    }


def _derive_key_signals(snap: SignalSnapshot) -> list[str]:
    signals = []
    if snap.rsi_14 is not None and snap.rsi_14 < 30:
        signals.append(f"RSI oversold at {snap.rsi_14}")
    if snap.rsi_divergence:
        signals.append("Bullish RSI divergence detected")
    if snap.macd_crossover:
        signals.append("MACD bullish crossover")
    if snap.bb_bounce:
        signals.append("Bollinger Band lower-band bounce")
    if snap.stoch_crossover:
        signals.append("Stochastic crossover in oversold zone")
    if snap.candle_pattern:
        signals.append(f"Bullish candlestick pattern: {snap.candle_pattern}")
    return signals[:3] or ["No significant reversal signals detected"]
