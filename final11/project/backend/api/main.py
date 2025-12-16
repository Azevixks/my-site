"""Minimal API for Stop Fake demo.

Exposes /analyze that accepts JSON {"text": "..."} and returns a verdict.
Працює лише через LLM (OpenAI). Якщо ключу немає або LLM недоступний —
повертає помилку сервісу.
"""
from __future__ import annotations

import logging
import os
from typing import Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv(".env", override=False)
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "info").upper(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("stopfake.api")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=10, description="News/article text to analyze")


class AnalyzeResponse(BaseModel):
    result: str
    confidence: float
    emotion: str
    reasons: List[str]
    sources: List[str]
    raw_model_output: Optional[dict] = None


app = FastAPI(title="Stop Fake API", version="0.1.0")

# Simple in-memory cache to стабілізувати результат для однакового тексту.
_ANALYZE_CACHE: Dict[str, AnalyzeResponse] = {}


async def _openai_score(text: str) -> AnalyzeResponse:
    """LLM-backed classifier. Requires OPENAI_API_KEY."""
    if not OPENAI_API_KEY:
        raise RuntimeError("OpenAI key not configured")

    system_prompt = (
        "Ти бот для виявлення фейкових новин українською. "
        "Класифікуй текст як fake / real / uncertain. "
        "Дай короткі причини та список емоцій (factual/emotional/mixed). "
        "Пояснення значень: "
        "confidence — ймовірність, що новина правдива (0=повністю фейк, 1=повністю правдива); "
        "emotion=factual — нейтральний/сухий виклад; "
        "emotion=emotional — емоційний або маніпулятивний тон; "
        "emotion=mixed — змішаний тон (є і фактологія, і емоційні елементи). "
        "Поверни рівно JSON-об'єкт із ключами: "
        "result, confidence (0-1), emotion, reasons (list), sources (list). "
        "Строго дотримуйся формату JSON."
    )

    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        # Максимально детермінований режим: однаковий текст → максимально стабільна відповідь.
        "temperature": 0.0,
        "top_p": 1.0,
        # Strict JSON schema to enforce shape.
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "verdict",
                "schema": {
                    "type": "object",
                    "properties": {
                        "result": {"type": "string", "enum": ["fake", "real", "uncertain"]},
                        "confidence": {"type": "number"},
                        "emotion": {"type": "string"},
                        "reasons": {"type": "array", "items": {"type": "string"}},
                        "sources": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["result", "confidence", "emotion", "reasons", "sources"],
                    "additionalProperties": False,
                },
            },
        },
    }

    logger.debug("Sending prompt to OpenAI model=%s text_len=%d", OPENAI_MODEL, len(text))
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json=payload,
        )

    if resp.status_code != 200:
        logger.warning("LLM error status=%s body=%s", resp.status_code, resp.text)
        raise HTTPException(status_code=502, detail=f"LLM error: {resp.text}")

    data = resp.json()
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        logger.warning("Unexpected LLM response structure: %s", data)
        raise HTTPException(status_code=502, detail="Unexpected LLM response") from exc

    # Best effort: the model returns JSON. If parsing fails, fall back to heuristic.
    import json

    try:
        parsed = json.loads(content)
        logger.debug("Parsed LLM JSON: %s", parsed)
        raw_result = str(parsed.get("result", "uncertain"))
        # Базовий confidence з відповіді моделі (як підказка)
        raw_conf = float(parsed.get("confidence", 0.5))
        raw_emotion = str(parsed.get("emotion", "mixed"))
        base_reasons = list(parsed.get("reasons", []))

        # Додаємо явне пояснення про роль тону.
        if raw_emotion == "emotional":
            tone_reason = "Емоційний/маніпулятивний тон тексту вплинув на зниження довіри до новини."
        elif raw_emotion == "factual":
            tone_reason = "Тон тексту переважно нейтральний/фактологічний, тому головну роль відіграють факти та джерела."
        else:  # mixed або інше
            tone_reason = "У тексті поєднуються емоційні елементи та фактична інформація; тон враховано під час оцінки."

        if tone_reason not in base_reasons:
            base_reasons.append(tone_reason)

        # Нормалізація: робимо відсотки однозначними й не «рандомними».
        # Це наш інтерпретований рівень довіри, а не сире значення моделі.
        if raw_result == "real":
            # Новина здебільшого правдива
            norm_conf = 0.9
        elif raw_result == "fake":
            # Новина здебільшого фейкова
            norm_conf = 0.1
        else:  # "uncertain" або будь-що інше
            # Модель не впевнена
            norm_conf = 0.5

        return AnalyzeResponse(
            result=raw_result,
            confidence=norm_conf,
            emotion=raw_emotion,
            reasons=base_reasons,
            sources=list(parsed.get("sources", [])),
            raw_model_output=data,
        )
    except Exception as exc:
        logger.info("LLM content not JSON. content=%s error=%s", content, exc)
        raise HTTPException(status_code=502, detail="LLM response parse error") from exc


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    """Main entrypoint for the extension."""
    text = req.text.strip()
    if len(text) < 10:
        raise HTTPException(status_code=400, detail="Text is too short")

    logger.info(
        "Analyze request len=%d openai=%s model=%s",
        len(text),
        bool(OPENAI_API_KEY),
        OPENAI_MODEL,
    )
    logger.debug("Analyze snippet=%s", text[:120].replace("\n", " "))

    # Якщо такий самий текст уже аналізувався — повертаємо закешований результат.
    if text in _ANALYZE_CACHE:
        logger.info("Cache hit for text_len=%d", len(text))
        return _ANALYZE_CACHE[text]

    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not configured; cannot process request")
        raise HTTPException(status_code=503, detail="LLM unavailable (missing OPENAI_API_KEY)")

    try:
        result = await _openai_score(text)
        _ANALYZE_CACHE[text] = result
        return result
    except Exception as exc:
        logger.exception("LLM path failed: %s", exc)
        raise HTTPException(status_code=502, detail="LLM temporarily unavailable") from exc


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    # Enable running via `python main.py`; uvicorn is still the recommended runner.
    import uvicorn

    logger.info("Starting dev server host=%s port=%s", os.getenv("HOST", "0.0.0.0"), os.getenv("PORT", 8000))
    uvicorn.run(
        app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        log_level=os.getenv("LOG_LEVEL", "info"),
    )
