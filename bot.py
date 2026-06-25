import asyncio
import json
import logging
import os
from datetime import datetime
import pytz

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from config import BOT_TOKEN, CHAT_IDS, TIMEZONE
from matches import get_todays_matches

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

SUBSCRIBERS_FILE = "subscribers.json"


def load_subscribers():
    if os.path.exists(SUBSCRIBERS_FILE):
        with open(SUBSCRIBERS_FILE, "r") as f:
            return set(json.load(f))
    # Стартові підписники з config.py
    return set(CHAT_IDS)


def save_subscribers(subs):
    with open(SUBSCRIBERS_FILE, "w") as f:
        json.dump(list(subs), f)


subscribers = load_subscribers()


def subscribe_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔔 Підписатись на розсилку", callback_data="subscribe")]
    ])


def unsubscribe_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔕 Відписатись від розсилки", callback_data="unsubscribe")]
    ])


async def send_daily_schedule(app: Application):
    # Ранкова розсилка — рахунок вже зіграних матчів прихований
    message = await get_todays_matches(hide_finished_scores=True)
    for chat_id in list(subscribers):
        try:
            await app.bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
            logger.info(f"Schedule sent to {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send to {chat_id}: {e}")


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in subscribers:
        keyboard = unsubscribe_keyboard()
        status = "Ти вже підписаний на щоденну розсилку о 9:00 ✅"
    else:
        keyboard = subscribe_keyboard()
        status = "Ти ще не підписаний на розсилку."

    await update.message.reply_text(
        f"🌍 <b>Бот розкладу ЧС-2026</b>\n\n"
        f"{status}\n\n"
        f"Команди:\n"
        f"/schedule — розклад матчів на сьогодні\n"
        f"/start — це повідомлення",
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def cmd_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Завантажую матчі ЧС-2026...")
    # На вимогу — показуємо повний рахунок
    message = await get_todays_matches(hide_finished_scores=False)
    await update.message.reply_text(message, parse_mode="HTML")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id

    if query.data == "subscribe":
        subscribers.add(chat_id)
        save_subscribers(subscribers)
        await query.edit_message_reply_markup(reply_markup=unsubscribe_keyboard())
        await query.message.reply_text(
            "🔔 Ти підписаний! Щодня о 9:00 отримуватимеш розклад матчів ЧС-2026."
        )

    elif query.data == "unsubscribe":
        subscribers.discard(chat_id)
        save_subscribers(subscribers)
        await query.edit_message_reply_markup(reply_markup=subscribe_keyboard())
        await query.message.reply_text(
            "🔕 Ти відписаний від розсилки. Можеш знову підписатись у будь-який момент."
        )


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
    logger.info(f"Scheduler started. WC-2026 daily at 09:00 {TIMEZONE}")


def main():
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("schedule", cmd_schedule))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
