"""
AI Brain - Claude yordamida vazifani tushunish
"""
 
import os
import json
import logging
from datetime import datetime, timedelta
import pytz
import anthropic
 
logger = logging.getLogger(__name__)
 
TASHKENT_TZ = pytz.timezone("Asia/Tashkent")
 
SYSTEM_PROMPT = """Sen O'zbekiston (Toshkent vaqti, UTC+5) da ishlaydigon shaxsiy kotibsan.
Foydalanuvchi o'zbek tilida vazifa yoki uchrashuv haqida aytadi.
Sening vazifang — bu ma'lumotni tahlil qilib, JSON formatida qaytarish.
 
BUGUNGI SANA VA VAQT: {current_datetime}
 
QOIDALAR:
1. Agar foydalanuvchi vazifa yoki uchrashuv qo'shmoqchi bo'lsa — action = "add_task"
2. Agar savol bersa yoki boshqa narsa desa — action = "info" va message maydonida javob ber
 
KATEGORIYALAR:
- "ish" — ish, loyiha, hisobot, email, xodimlar, biznes
- "shaxsiy" — shaxsiy ishlar, oila, soglik, do'stlar
- "uchrashuv" — meeting, uchrashuv, ko'rishish, suhbat
 
MUHIMLIK:
- urgent: true — "muhim", "shoshilinch", "bugun albatta", "urgent" kabi so'zlar bo'lsa
- urgent: false — oddiy holat
 
VAQT ANIQLASH:
- "ertaga" = ertangi kun
- "juma kuni" = kelayotgan juma
- "bu hafta" = joriy haftaning oxiri (juma)
- "keyinroq", "vaqt bo'lganda" = 1 hafta keyin
- Agar vaqt aytilmasa — bugungi sanani ishlat, vaqt: null
 
JAVOB FORMATI (faqat JSON, hech qanday izoh yo'q):
 
add_task uchun:
{
  "action": "add_task",
  "event": {
    "title": "qisqa va aniq sarlavha",
    "date_iso": "2025-01-15",
    "time_iso": "10:00" yoki null,
    "date_str": "15 yanvar, chorshanba",
    "time_str": "soat 10:00" yoki "",
    "category": "ish" | "shaxsiy" | "uchrashuv",
    "urgent": true | false,
    "urgency_label": "🔴 Shoshilinch" | "🟢 Oddiy",
    "note": "qo'shimcha ma'lumot yoki null"
  }
}
 
info uchun:
{
  "action": "info",
  "message": "foydalanuvchiga javob matni"
}
"""
 
 
class AIBrain:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY topilmadi!")
        self.client = anthropic.Anthropic(api_key=api_key)
 
    async def analyze(self, user_text: str) -> dict:
        """Foydalanuvchi matnini tahlil qilish"""
        now = datetime.now(TASHKENT_TZ)
        current_datetime = now.strftime("%Y-%m-%d %A, soat %H:%M (Toshkent vaqti)")
 
        # O'zbek kunlarini almashtirish (agar kerak bo'lsa)
        day_map = {
            "Monday": "Dushanba", "Tuesday": "Seshanba", "Wednesday": "Chorshanba",
            "Thursday": "Payshanba", "Friday": "Juma", "Saturday": "Shanba", "Sunday": "Yakshanba"
        }
        for eng, uzb in day_map.items():
            current_datetime = current_datetime.replace(eng, uzb)
 
        system = SYSTEM_PROMPT.format(current_datetime=current_datetime)
 
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                system=system,
                messages=[{"role": "user", "content": user_text}]
            )
 
            raw = response.content[0].text.strip()
            logger.info(f"Claude javobi: {raw[:200]}")
 
            # JSON tozalash
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()
 
            result = json.loads(raw)
            return result
 
        except json.JSONDecodeError as e:
            logger.error(f"JSON xatosi: {e}, raw: {raw}")
            return {
                "action": "info",
                "message": "Kechirasiz, tushunishda xatolik yuz berdi. Boshqacha aytib ko'ring."
            }
        except Exception as e:
            logger.error(f"Claude xatosi: {e}")
            return {
                "action": "info",
                "message": "Xatolik yuz berdi. Bir oz kutib qaytadan urinib ko'ring."
