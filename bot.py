import asyncio
import logging
from datetime import datetime
import pytz

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram.ext import Application, CommandHandler

from config import BOT_TOKEN, CHAT_IDS, TIMEZONE
from matches import get_todays_matches

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def send_daily_schedule(app: Application):
    message = await get_todays_matches()
    for chat_id in CHAT_IDS:
        try:
            await app.bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
            logger.info(f"Schedule sent to chat {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send to {chat_id}: {e}")


async def cmd_start(update, context):
    await update.message.reply_text(
        "🌍 Привіт! Я слідкую за матчами <b>Чемпіонату світу 2026</b> і щодня о 9:00 надсилаю розклад.\n\n"
        "Команди:\n"
        "/schedule — розклад матчів ЧС-2026 на сьогодні\n"
        "/start — це повідомлення",
        parse_mode="HTML"
    )


async def cmd_schedule(update, context):
    await update.message.reply_text("⏳ Завантажую матчі ЧС-2026...")
    message = await get_todays_matches()
    await update.message.reply_text(message, parse_mode="HTML")


async def post_init(app: Application):
    tz = pytz.timezone(TIMEZONE)
    scheduler = AsyncIOScheduler(timezone=tz)
    scheduler.add_job(
        send_daily_schedule,
        trigger="cron",
        hour=9,
        minute=0,
        args=[app],
    )
    scheduler.start()
    logger.info(f"Scheduler started. WC-2026 daily messages at 09:00 {TIMEZONE}")


def main():
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("schedule", cmd_schedule))
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
