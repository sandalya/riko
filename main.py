"""Drone-recon Telegram bot — точка входу."""
import logging
import sys
from telegram.ext import Application
from core.config import BOT_TOKEN, LOGS_DIR, DATA_INPUT_DIR, DATA_OUTPUT_DIR

LOGS_DIR.mkdir(exist_ok=True)
DATA_INPUT_DIR.mkdir(parents=True, exist_ok=True)
DATA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "bot.log"),
        logging.StreamHandler(),
    ],
)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("main")


async def error_handler(update: object, context):
    log.error(f"Помилка: {context.error}")


def main():
    if not BOT_TOKEN:
        log.error("BOT_TOKEN не встановлено")
        sys.exit(1)

    from bot.client import setup_handlers

    log.info("Drone-recon стартує...")

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .build()
    )

    setup_handlers(app)
    app.add_error_handler(error_handler)

    log.info("Polling запущено")
    app.run_polling(
        drop_pending_updates=True,
        poll_interval=1.0,
        timeout=20,
    )


if __name__ == "__main__":
    main()
