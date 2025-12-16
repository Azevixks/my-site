**Призначення:** REST API для аналізу новин/статей.

## Швидкий старт
```bash
cd project/backend/api
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Перевірка: `http://localhost:8000/health`.

## Виклик /analyze
```
POST http://localhost:8000/analyze
Content-Type: application/json

{ "text": "Тут текст новини..." }
```

Приклад відповіді:
```json
{
  "result": "fake | real | uncertain",
  "confidence": 0.73,
  "emotion": "emotional",
  "reasons": ["Багато емоційних слів", "Немає посилань на джерела"],
  "sources": []
}
```

## OpenAI (необов'язково)
- Додайте `OPENAI_API_KEY` (і за бажанням `OPENAI_MODEL`) у змінні оточення.
- Якщо ключа немає, API використовує прості евристики, щоб проєкт працював офлайн.

## Структура
- `main.py` – FastAPI застосунок з ендпоінтами `/analyze` та `/health`.
- `requirements.txt` – залежності.