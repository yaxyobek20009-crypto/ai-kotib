import os
import logging
import asyncio
from datetime import datetime, time
import pytz

from telegram import Update, BotCommand
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes
)

from ai_brain import AIBrain
from calendar_service import CalendarService
from voice_handler import VoiceHandler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TASHKENT_TZ = pytz.timezone("Asia/Tashkent")
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", "0"))


def is_allowed(user_id):
    if ALLOWED_USER_ID == 0:
        return True
    return user_id == ALLOWED_USER_ID


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return
    text = (
        "Assalomu alaykum! Men sizning shaxsiy kotibingizman\n\n"
        "Menga shunchaki aytishingiz kifoya, masalan:\n"
        "Ertaga soat 10 da Alisher bilan uchrashuv bor\n"
        "Juma kuni hisobotni topshirish kerak, muhim\n"
        "Bu hafta doktorga borish kerak, shaxsiy\n\n"
        "Ovozli xabar ham yubora olasiz\n\n"
        "/vazifalar - bugungi vazifalar\n"
        "/hafta - bu haftaning rejasi\n"
        "/yordam - batafsil korsatmalar"
    )
    await update.message.reply_text(text)


async def yordam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return
    text = (
        "AI Kotib - Yoriqnoma\n\n"
        "Vazifa qoshish:\n"
        "Oddiygina yozing yoki ovozli xabar yuboring.\n\n"
        "Kategoriyalar:\n"
        "Ish | Shaxsiy | Uchrashuv\n\n"
        "Muhimlik:\n"
        "Urgent - bugun hal qilinishi kerak\n"
        "Normal - oddiy vazifa\n\n"
        "Komandalar:\n"
        "/vazifalar - bugungi vazifalar\n"
        "/hafta - bu haftaning rejasi\n\n"
        "Har kuni ertalab soat 7:00 da kunlik reja yuboraman"
    )
    await update.message.reply_text(text)


async def bugungi_vazifalar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return
    await update.message.reply_text("Bugungi vazifalarni yuklamoqda...")
    cal = CalendarService()
    events = cal.get_today_events()
    msg = format_events(events, "Bugungi vazifalar")
    await update.message.reply_text(msg)


async def haftalik_reja(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return
    await update.message.reply_text("Haftalik rejani yuklamoqda...")
    cal = CalendarService()
    events = cal.get_week_events()
    msg = format_events(events, "Bu haftaning rejasi")
    await update.message.reply_text(msg)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return
    user_text = update.message.text
    thinking_msg = await update.message.reply_text("Tushunmoqda...")
    brain = AIBrain()
    result = await brain.analyze(user_text)
    reply = await process_result(result)
    await thinking_msg.delete()
    await update.message.reply_text(reply)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return
    thinking_msg = await update.message.reply_text("Ovozni tinglayapman...")
    voice_handler = VoiceHandler()
    voice_file = await update.message.voice.get_file()
    voice_bytes = await voice_file.download_as_bytearray()
    text = await voice_handler.transcribe(bytes(voice_bytes))
    if not text:
        await thinking_msg.delete()
        await update.message.reply_text("Ovozni tushuna olmadim. Qaytadan urinib koring.")
        return
    await thinking_msg.edit_text(f"Eshitdim: {text}\n\nTushunmoqda...")
    brain = AIBrain()
    result = await brain.analyze(text)
    reply = await process_result(result)
    await thinking_msg.delete()
    await update.message.reply_text(f"Ovoz: {text}\n\n{reply}")


async def process_result(result: dict) -> str:
    if result["action"] == "add_task":
        cal = CalendarService()
        success = cal.add_event(result["event"])
        if success:
            ev = result["event"]
            urgent = "Shoshilinch" if ev.get("urgent") else "Oddiy"
            cat = ev.get("category", "ish").capitalize()
            reply = f"Qoshildi!\n\n{ev['title']}\n{ev['date_str']}\n{urgent}\n{cat}"
            if ev.get("note"):
                reply += f"\n{ev['note']}"
        else:
            reply = "Kalendarga qoshishda xatolik. Qaytadan urinib koring."
    else:
        reply = result.get("message", "Tushunmadim. Boshqacha aytib koring.")
    return reply


async def send_morning_summary(context: ContextTypes.DEFAULT_TYPE):
    if ALLOWED_USER_ID == 0:
        return
    cal = CalendarService()
    events = cal.get_today_events()
    if not events:
        msg = "Xayrli tong!\n\nBugun uchun rejalashtirilgan vazifalar yoq. Yaxshi kun!"
    else:
        msg = format_events(events, "Xayrli tong! Bugungi reja")
    await context.bot.send_message(chat_id=ALLOWED_USER_ID, text=msg)


def format_events(events: list, title: str) -> str:
    if not events:
        return f"{title}\n\nHozircha hech narsa yoq."
    lines = [f"{title}\n"]
    for ev in events:
        urgent = "[!]" if ev.get("urgent") else ""
        time_part = f" - {ev['time_str']}" if ev.get("time_str") else ""
        lines.append(f"{urgent} {ev['title']}{time_part}")
    return "\n".join(lines)


async def post_init(application: Application):
    commands = [
        BotCommand("start", "Boshqatdan boshlash"),
        BotCommand("vazifalar", "Bugungi vazifalar"),
        BotCommand("hafta", "Bu haftaning rejasi"),
        BotCommand("yordam", "Yordam"),
    ]
    await application.bot.set_my_commands(commands)
    morning_time = time(hour=7, minute=0, tzinfo=TASHKENT_TZ)
    application.job_queue.run_daily(send_morning_summary, time=morning_time)


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN topilmadi!")

    app = (
        Application.builder()
        .token(token)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("yordam", yordam))
    app.add_handler(CommandHandler("vazifalar", bugungi_vazifalar))
    app.add_handler(CommandHandler("hafta", haftalik_reja))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    logger.info("Bot ishga tushdi")
    app.run_polling(drop_pending_updates=True, close_loop=False)


if __name__ == "__main__":
    main()
