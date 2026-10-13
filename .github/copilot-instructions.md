# Project Instructions

- This project uses Python 3.11+, aiogram 3, APScheduler 3, and gspread.
- Keep Telegram handlers asynchronous; run blocking Google Sheets operations with `asyncio.to_thread`.
- Read secrets from `.env` and never commit credentials or service-account JSON files.
- Keep user-facing bot text and README content in Russian.
- Run `python -m unittest discover -s tests -v` for tests when Python is available.
