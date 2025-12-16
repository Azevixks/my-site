# Stop Fake (demo)

Простий MVP: Python API + Chrome Extension.

## Backend
1) `cd project/backend/api`
2) `python -m venv .venv && .venv\Scripts\activate`
3) `pip install -r requirements.txt`
4) Запустити: `uvicorn main:app --reload --host 0.0.0.0 --port 8000`
5) Перевірка: `http://localhost:8000/health`

Опційно: задайте `OPENAI_API_KEY` (і `OPENAI_MODEL`) — тоді /analyze використовує OpenAI, інакше працює локальна евристика.

## Chrome Extension
1) Відкрийте `chrome://extensions/`
2) Увімкніть Developer mode → `Load unpacked`
3) Виберіть папку `project/extension`
4) На сторінці новини натисніть іконку Stop Fake. Автоаналіз вмикається в опціях.

Файли:
- `project/backend/api/main.py` – FastAPI /analyze
- `project/extension/manifest.json` – конфігурація розширення
- `project/extension/popup/*` – UI результату
- `project/extension/options_page/*` – налаштування



