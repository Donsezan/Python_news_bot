import os
import sys
import time
from datetime import datetime, timedelta, date

from fetching_data import FetchingData
from ai.ai_service import AIService
from telegram_service import TelegramService
from data_service import DataService
from ai.ai_provider import AIProvider


def _load_env():
    try:
        with open('.env') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, _, value = line.partition('=')
                    os.environ.setdefault(key.strip(), value.strip().strip('"\''))
    except FileNotFoundError:
        pass


_load_env()
HEADERS = {"User-Agent": "Mozilla/5.0"}
DB_PATH = "./news_bot.db"
SIMILARITY_THRESHOLD = 0.85
DISTANCE_THRESHOLD = 1 - SIMILARITY_THRESHOLD
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
NEWS_URL = os.getenv('NEWS_URL')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

_missing = [k for k, v in {'BOT_TOKEN': BOT_TOKEN, 'CHAT_ID': CHAT_ID, 'NEWS_URL': NEWS_URL, 'GEMINI_API_KEY': GEMINI_API_KEY}.items() if not v]
if _missing:
    raise EnvironmentError(f"Missing required environment variables: {', '.join(_missing)}")

# Toggle between AI providers: AIProvider.OPENAI or AIProvider.GEMINI
current_ai_provider = AIProvider.GEMINI

# Initialize services
data_service = DataService(db_path=DB_PATH, DISTANCE_THRESHOLD=DISTANCE_THRESHOLD)
fetch_service = FetchingData(NEWS_URL, HEADERS)
telegram_service = TelegramService(BOT_TOKEN, CHAT_ID)
ai_service = AIService.get_service(provider=current_ai_provider, gemini_api_key=GEMINI_API_KEY)


def _with_retry(fn, retries=3, delay=180):
    for attempt in range(1, retries + 1):
        try:
            return fn()
        except Exception as e:
            print(f"LLM error (attempt {attempt}/{retries}): {e}")
            if attempt < retries:
                print(f"Retrying in {delay}s...")
                time.sleep(delay)
    return None


def job(dry_run=False):
    print("Fetching latest articles...")
    new_articles = fetch_service.fetch_latest_articles()
    print(f"Found {len(new_articles)} new articles.")
    for title, href in new_articles:
        print(f"Processing article: {title}")
        if not data_service.is_new_article(title):
            print(f"Article '{title}' already processed, skipping.")
            continue

        print("Fetching and summarizing article...")
        result = fetch_service.fetch_and_summarize(title, href)
        if not result:
            print("Failed to fetch and summarize article.")
            continue

        main_content, images, date_time = result
        if not main_content or not date_time:
            print("Article content or date/time is missing.")
            continue

        if not dry_run:
            print("Saving article...")
            data_service.save_article(title, date_time)

        print("Evaluating article...")
        article_score = _with_retry(lambda: ai_service.evaluate_article(title))
        if not article_score:
            print(f"Failed to evaluate article '{title}'. Skipping.")
            continue

        print(f"Article score: {article_score}")
        if article_score < 6:
            print(f"Article '{title}' with score '{article_score}' does not meet the evaluation criteria. Skipping.")
            continue

        print("Summarizing with emojis...")
        evaluated_content = _with_retry(lambda: ai_service.summarize_with_emojis(main_content, target_language='en'))

        if evaluated_content is None:
            print(f"Failed to summarize article '{title}' with emojis. Skipping.")
            continue

        if not dry_run:
            print("Posting to Telegram...")
            result_of_post = telegram_service.post_to_telegram(f"<b>{title}</b>\n\n{evaluated_content}", images, href)
            if not result_of_post:
                print(f"Failed to post article '{title}' to Telegram.")
                continue
        time.sleep(600)
    print("Job finished.")


if __name__ == "__main__":
    dry_run = '--dry-run' in sys.argv
    job(dry_run=dry_run)
    if dry_run:
        sys.exit(0)

    next_job = datetime.now() + timedelta(minutes=10)
    last_cleanup_day = date.today()

    while True:
        time.sleep(60)
        now = datetime.now()
        print(f"All done for {now.strftime('%Y-%m-%d %H:%M:%S')}")

        if now.date() > last_cleanup_day:
            data_service.cleanup_old_articles(max_age_days=10)
            last_cleanup_day = now.date()

        if now >= next_job:
            job(dry_run=False)
            next_job = now + timedelta(minutes=10)
