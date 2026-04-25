# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A news aggregation bot that scrapes Málaga news articles, evaluates their relevance using AI, and posts curated content to a Telegram channel. The bot runs on a 10-minute scheduler.

## Commands

### Setup
```bash
source .venv/bin/activate       # Activate virtual environment
```

### Run
```bash
python3 main.py                 # Start the bot (runs indefinitely via scheduler)
```

### Tests
```bash
python3 -m unittest discover -s tests -p "test_*.py"   # Run all tests
python3 -m unittest tests.test_ai_services              # Run specific test module
```

### Lint
No linter is configured. Use `flake8` or `ruff` if needed.

## Architecture

The bot runs a scheduled `job()` function in [main.py](main.py) every 10 minutes:

1. **Fetch** — [fetching_data.py](fetching_data.py) scrapes article links and content from the news source via BeautifulSoup
2. **Deduplicate** — [data_service.py](data_service.py) checks ChromaDB (vector store) for similar articles using cosine distance threshold of 0.15
3. **Evaluate** — AI service scores article relevance 0–10; articles scoring below 6 are skipped
4. **Summarize** — AI service generates an emoji-rich Telegram-ready summary
5. **Post** — [telegram_service.py](telegram_service.py) sends media groups (up to 9 images) or text to the Telegram channel
6. **Cleanup** — Daily job removes ChromaDB entries older than 10 days

### AI Provider Abstraction (`ai/`)

Factory pattern with pluggable providers:
- [ai_service.py](ai/ai_service.py) — `AIService.get_service(provider)` factory
- [base_ai_service.py](ai/base_ai_service.py) — Abstract base with `evaluate()` and `summarize()` methods
- [gemini_service.py](ai/gemini_service.py) — Google Gemini (`gemini-2.0-flash`), uses JSON schema validation
- [openai_service.py](ai/openai_service.py) — OpenAI or local LM Studio (`http://localhost:1234/v1`)
- [ai_prompts.py](ai/ai_prompts.py) — All prompt templates
- [ai_provider.py](ai/ai_provider.py) — `AIProvider` enum (`GEMINI`, `OPENAI`)

Switch providers by changing `AIProvider.GEMINI` / `AIProvider.OPENAI` in [main.py](main.py).

### Key Configuration

All credentials live in `.env`:
```
BOT_TOKEN      # Telegram bot token
CHAT_ID        # Target Telegram channel/chat
NEWS_URL       # Source URL (malagahoy.es/malaga/)
GEMINI_API_KEY # Google Generative AI key
```

Constants in [main.py](main.py):
- `CHROMA_DB_PATH = "./chroma_db_persistence"` — vector DB location
- `SIMILARITY_THRESHOLD = 0.85` (distance = 0.15) — duplicate detection cutoff

### Response Parsing

[response_parser.py](response_parser.py) extracts structured data (scores, summaries) from AI responses using both JSON parsing and regex fallback. AI responses are validated against JSON schemas defined per-provider in the `ai/` module.

## Dependencies

No `requirements.txt` exists. Key packages (installed in `.venv`):
- `google-generativeai` — Gemini API
- `openai` — OpenAI/LM Studio client
- `chromadb` — Vector database for deduplication
- `beautifulsoup4` + `requests` — Web scraping
- `schedule` — Job scheduling
- `python-dotenv` — Environment variable loading
- `python-telegram-bot` — Telegram API

## Testing

Tests use `unittest` with `unittest.mock` to mock AI provider clients. Tests cover `evaluate()` and `summarize()` for both providers. No integration tests — all tests mock external API calls.
