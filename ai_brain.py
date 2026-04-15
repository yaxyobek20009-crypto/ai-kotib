# 🤖 AI Kotib — Sozlash Yo'riqnomasi

## 1-QADAM: Anthropic API kaliti olish

1. https://console.anthropic.com ga kiring
2. "API Keys" → "Create Key" bosing
3. Kalitni nusxalab oling (sk-ant-... bilan boshlanadi)

---

## 2-QADAM: Google Calendar sozlash

### A) Google Cloud Console
1. https://console.cloud.google.com ga kiring
2. Yangi loyiha yarating (masalan: "ai-kotib")
3. "APIs & Services" → "Enable APIs" → "Google Calendar API" yoqing

### B) Service Account yaratish
1. "APIs & Services" → "Credentials" ga kiring
2. "Create Credentials" → "Service Account" tanlang
3. Istalgan nom bering, "Create" bosing
4. Yaratilgan service account ni oching
5. "Keys" tab → "Add Key" → "JSON" tanlang
6. JSON fayl yuklab olinadi — buni saqlang!

### C) Kalendarni ulash
1. Google Calendar ni oching (calendar.google.com)
2. Kerakli kalendarning sozlamalariga kiring (uch nuqta → "Settings")
3. "Share with specific people" → service account emailini qo'shing
   (JSON fayldan `client_email` maydoni, masalan: ai-kotib@project.iam.gserviceaccount.com)
4. Ruxsat: "Make changes to events"
5. Calendar ID ni topib oling: sozlamalar → "Integrate calendar" → Calendar ID

---

## 3-QADAM: Telegram Bot ID olish

1. Telegramda @userinfobot ga yozing
2. `/start` yuboring
3. U sizning user ID ingizni ko'rsatadi (raqam, masalan: 123456789)

---

## 4-QADAM: Railway da deploy qilish

### A) Railway.app
1. https://railway.app ga kiring (GitHub bilan kiring)
2. "New Project" → "Deploy from GitHub repo" tanlang
3. Bu papkani GitHub ga yuklang, keyin tanlang

### B) Environment Variables qo'shish
Railway dashboard → loyiha → "Variables" bo'limi:

```
TELEGRAM_BOT_TOKEN     = 7xxxxxxxx:AAF...  (BotFather dan)
ANTHROPIC_API_KEY      = sk-ant-api03-...  (Anthropic Console dan)
OPENAI_API_KEY         = sk-proj-...       (platform.openai.com dan)
GOOGLE_CALENDAR_ID     = xxx@group.calendar.google.com (yoki primary)
ALLOWED_USER_ID        = 123456789         (sizning Telegram ID ingiz)
GOOGLE_CREDENTIALS_JSON = {...}            (JSON faylning butun mazmuni)
```

> ⚠️ `GOOGLE_CREDENTIALS_JSON` uchun JSON faylni oching,
> barcha mazmunini nusxalab, bir qator sifatida yapishtirib qo'ying.

### C) Start Command
Railway → Settings → "Start Command":
```
python bot.py
```

---

## 5-QADAM: Botni tekshirish

Telegram da botingizga yozing:
- `/start` — ishga tushishi kerak
- `Ertaga soat 10 da Alisher bilan uchrashuv bor` — qo'shilishi kerak
- `/vazifalar` — bugungi vazifalar chiqishi kerak

---

## Xatoliklar haqida

**Bot javob bermasa:**
- Railway logs ni tekshiring
- TELEGRAM_BOT_TOKEN to'g'riligini tekshiring

**"GOOGLE_CREDENTIALS_JSON topilmadi":**
- JSON ni to'g'ri yapishtirgansizmi?

**"ANTHROPIC_API_KEY topilmadi":**
- Anthropic Console dan yangi kalit oling

---

## Narxlar (taxminiy)

| Xizmat | Narx |
|--------|------|
| Railway | $5/oy (Hobby plan) |
| Anthropic API | ~$0.001 per so'rov |
| OpenAI Whisper | ~$0.006/min ovoz |
| Google Calendar API | Bepul |

Kuniga 50 ta so'rov yuborilsa — taxminan $5-8/oy.
