"""GenAI calls — NVIDIA NIM only (free tier, single vendor). Retries with backoff on
transient failures (timeouts, 429/5xx), fails soft instead of throwing a raw 500
to the client if NIM is genuinely unavailable.
"""
import logging

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from backend.shared.config import get_settings

logger = logging.getLogger("stadiumpulse.genai")
settings = get_settings()

RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class NimUnavailableError(Exception):
    """Raised when NIM is unreachable after retries — callers should degrade gracefully."""


def _is_retryable(exc: Exception) -> bool:
    if isinstance(exc, httpx.TimeoutException):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in RETRYABLE_STATUS
    return False


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError)),
    reraise=True,
)
async def _nim_chat_raw(system: str, user: str, max_tokens: int) -> str:
    async with httpx.AsyncClient(timeout=settings.nim_timeout_seconds) as client:
        resp = await client.post(
            f"{settings.nvidia_nim_base_url}/chat/completions",
            headers={"Authorization": f"Bearer {settings.nvidia_nim_api_key}"},
            json={
                "model": settings.nim_chat_model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "max_tokens": max_tokens,
                "temperature": 0.3,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()


async def _nim_chat(system: str, user: str, max_tokens: int = 512) -> str:
    if not settings.nvidia_nim_api_key:
        return f"[dev mode — set NVIDIA_NIM_API_KEY] {user[:200]}"

    try:
        return await _nim_chat_raw(system, user, max_tokens)
    except (httpx.TimeoutException, httpx.HTTPStatusError) as exc:
        logger.warning("NIM call failed after retries: %s", exc)
        raise NimUnavailableError("NVIDIA NIM is temporarily unavailable") from exc


async def translate(text: str, target_lang: str) -> str:
    """Translate via NVIDIA NIM. On failure, returns original text rather than erroring —
    a fan seeing untranslated English beats a broken chat.
    """
    if target_lang == "en" and text.isascii():
        return text
    try:
        return await _nim_chat(
            system=f"Translate the user's text to {target_lang}. Output only the translation, nothing else.",
            user=text,
        )
    except NimUnavailableError:
        return text


async def reason(prompt: str) -> str:
    """Recommended-action / navigator answer generation via NVIDIA NIM.
    Raises NimUnavailableError on failure — callers decide how to surface that
    (e.g. a friendly 503 rather than a stack trace).
    """
    return await _nim_chat(
        system="You are a concise, operational assistant for a stadium platform.",
        user=prompt,
    )


# Backwards-compat export some call sites still check directly.
NIM_API_KEY = settings.nvidia_nim_api_key
