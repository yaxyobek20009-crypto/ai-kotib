"""
AI Kotib - Telegram Bot
Akangiz uchun sun'iy intellektli shaxsiy kotib
"""

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

# Logging sozlash
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Timezone
TASHKENT_TZ = pytz.timezone("Asia/Tashkent")

# Faqat akangiz foydalanishi uchun
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", "0"))


def is_allowed(user_id: int) -> bool:
    """Faqat ruxsat etilgan foydalanuvchi"""
    if ALLOWED_USER_ID == 0:
        return True  # Sozlanmagan bo'lsa, hamma kirishi mumkin
    return user_id == ALLOWED_USER_ID


# ─────────────────────────────────────────
# KOMANDALAR
# ─────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return
    text = (
        "Assalomu alaykum! Men sizning shaxsiy kotibingizman 🤖\n\n"
        "Menga shunchaki aytishingiz kifoya, masalan:\n"
        "• «Ertaga soat 10 da Alisher bilan uchrashuv bor»\n"
        "• «Juma kuni hisobotni topshirish kerak, muhim»\n"
        "• «Bu hafta doktorga borish kerak, shaxsiy»\n\n"
        "Ovozli xabar ham yubora olasiz 🎤\n\n"
        "📋 /vazifalar — bugungi vazifalar\n"
        "📅 /hafta — bu haftaning rejasi\n"
        "❓ /yordam — batafsil ko'rsatmalar"
    )
    await update.message.reply_text(text)


async def yordam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return
    text = (
        "🤖 *AI Kotib — Yo'riqnoma*\n\n"
        "*Vazifa qo'shish:*\n"
        "Oddiygina yozing yoki ovozli xabar yuboring.\n"
        "Kategoriya, muhimlik va vaqtni men o'zim aniqlayman.\n\n"
        "*Kategoriyalar:*\n"
        "💼 Ish | 👤 Shaxsiy | 🤝 Uchrashuv\n\n"
        "*Muhimlik:*\n"
        "🔴 Urgent — bugun hal qilinishi kerak\n"
        "🟢 Normal — oddiy vazifa\n\n"
        "*Komandalar:*\n"
        "/vazifalar — bugungi vazifalar\n"
        "/hafta — bu haftaning rejasi\n"
        "/start — boshqatdan boshlash\n\n"
        "Har kuni ertalab soat 7:00 da kunlik reja yuboraman 📋"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def bugungi_vazifalar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return
    await update.message.reply_text("⏳ Bugungi vazifalarni yuklamoqda...")
    cal = CalendarService()
    events = cal.get_today_events()
    msg = format_events(events, "📋 Bugungi vazifalar")
    await update.message.reply_text(msg, parse_mode="Markdown")


async def haftalik_reja(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return
    await update.message.reply_text("⏳ Haftalik rejani yuklamoqda...")
    cal = CalendarService()
    events = cal.get_week_events()
    msg = format_events(events, "📅 Bu haftaning rejasi")
    await update.message.reply_text(msg, parse_mode="Markdown")


# ─────────────────────────────────────────
# MATN XABARLARNI QAYTA ISHLASH
# ─────────────────────────────────────────

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return

    user_text = update.message.text
    logger.info(f"Matn keldi: {user_text[:50]}")

    thinking_msg = await update.message.reply_text("🧠 Tushunmoqda...")

    brain = AIBrain()
    result = await brain.analyze(user_text)

    if result["action"] == "add_task":
        cal = CalendarService()
        success = cal.add_event(result["event"])

        if success:
            emoji = "🔴" if result["event"]["urgent"] else "🟢"
            cat_emoji = {"ish": "💼", "shaxsiy": "👤", "uchrashuv": "🤝"}.get(
                result["event"]["category"], "📌"
            )
            reply = (
                f"✅ Qo'shildi!\n\n"
                f"{cat_emoji} *{result['event']['title']}*\n"
                f"📅 {result['event']['date_str']}\n"
                f"{emoji} {result['event']['urgency_label']}\n"
                f"🏷 {result['event']['category'].capitalize()}"
            )
            if result["event"].get("note"):
                reply += f"\n📝 {result['event']['note']}"
        else:
            reply = "❌ Kalendarga qo'shishda xatolik. Qaytadan urinib ko'ring."

    elif result["action"] == "info":
        reply = result["message"]

    else:
        reply = result.get("message", "Tushunmadim. Iltimos, boshqacha tushuntiring.")

    await thinking_msg.delete()
    await update.message.reply_text(reply, parse_mode="Markdown")


# ─────────────────────────────────────────
# OVOZLI XABARLARNI QAYTA ISHLASH
# ─────────────────────────────────────────

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return

    logger.info("Ovozli xabar keldi")
    thinking_msg = await update.message.reply_text("🎤 Ovozni tinglayapman...")

    voice_handler = VoiceHandler()
    voice_file = await update.message.voice.get_file()
    voice_bytes = await voice_file.download_as_bytearray()

    text = await voice_handler.transcribe(bytes(voice_bytes))

    if not text:
        await thinking_msg.delete()
        await update.message.reply_text("❌ Ovozni tushuna olmadim. Qaytadan urinib ko'ring.")
        return

    await thinking_msg.edit_text(f"🎤 Eshitdim: _{text}_\n\n🧠 Tushunmoqda...", parse_mode="Markdown")

    # Matn kabi davom etish
    brain = AIBrain()
    result = await brain.analyze(text)

    if result["action"] == "add_task":
        cal = CalendarService()
        success = cal.add_event(result["event"])

        if success:
            emoji = "🔴" if result["event"]["urgent"] else "🟢"
            cat_emoji = {"ish": "💼", "shaxsiy": "👤", "uchrashuv": "🤝"}.get(
                result["event"]["category"], "📌"
            )
            reply = (
                f"✅ Qo'shildi!\n\n"
                f"🎤 _\"{text}\"_\n\n"
                f"{cat_emoji} *{result['event']['title']}*\n"
                f"📅 {result['event']['date_str']}\n"
                f"{emoji} {result['event']['urgency_label']}\n"
                f"🏷 {result['event']['category'].capitalize()}"
            )
        else:
            reply = "❌ Kalendarga qo'shishda xatolik."
    else:
        reply = result.get("message", "Tushunmadim.")

    await thinking_msg.delete()
    await update.message.reply_text(reply, parse_mode="Markdown")


# ─────────────────────────────────────────
# ERTALABKI XULOSA (SCHEDULED)
# ─────────────────────────────────────────

async def send_morning_summary(context: ContextTypes.DEFAULT_TYPE):
    """Har kuni 07:00 da yuboriladi"""
    if ALLOWED_USER_ID == 0:
        return

    cal = CalendarService()
    events = cal.get_today_events()

    if not events:
        msg = "🌅 Xayrli tong!\n\nBugun uchun rejalashtirilgan vazifalar yo'q. Yaxshi kun! 😊"
    else:
        msg = format_events(events, "🌅 Xayrli tong! Bugungi reja")

    await context.bot.send_message(
        chat_id=ALLOWED_USER_ID,
        text=msg,
        parse_mode="Markdown"
    )


# ─────────────────────────────────────────
# YORDAMCHI FUNKSIYALAR
# ─────────────────────────────────────────

def format_events(events: list, title: str) -> str:
    if not events:
        return f"{title}\n\n📭 Hozircha hech narsa yo'q."

    lines = [f"{title}\n"]
    for ev in events:
        emoji = "🔴" if ev.get("urgent") else "🟢"
        cat_emoji = {"ish": "💼", "shaxsiy": "👤", "uchrashuv": "🤝"}.get(
            ev.get("category", ""), "📌"
        )
        time_str = ev.get("time_str", "")
        time_part = f" — {time_str}" if time_str else ""
        lines.append(f"{emoji}{cat_emoji} *{ev['title']}*{time_part}")

    return "\n".join(lines)


# ─────────────────────────────────────────
# ASOSIY FUNKSIYA
# ─────────────────────────────────────────

async def post_init(application: Application):
    """Bot komandalarini ro'yxatga olish"""
    commands = [
        BotCommand("start", "Boshqatdan boshlash"),
        BotCommand("vazifalar", "Bugungi vazifalar"),
        BotCommand("hafta", "Bu haftaning rejasi"),
        BotCommand("yordam", "Yordam"),
    ]
    await application.bot.set_my_commands(commands)

    # Ertalab 07:00 da xulosa yuborish (Toshkent vaqti)
    job_queue = application.job_queue
    morning_time = time(hour=7, minute=0, tzinfo=TASHKENT_TZ)
    job_queue.run_daily(send_morning_summary, time=morning_time)
    logger.info("Ertalabki xulosa 07:00 da sozlandi (Toshkent vaqti)")


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

    # Handlerlar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("yordam", yordam))
    app.add_handler(CommandHandler("vazifalar", bugungi_vazifalar))
    app.add_handler(CommandHandler("hafta", haftalik_reja))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    logger.info("Bot ishga tushdi ✅")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
