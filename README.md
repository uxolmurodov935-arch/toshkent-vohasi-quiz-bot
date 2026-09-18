# Toshkent Vohasi Viktorina Boti

Bu bot `@toshkent_vohasi` kanaliga har kuni quyidagi vaqtlarda viktorina joylaydi:

- 09:00
- 11:00
- 14:00
- 16:00
- 18:00

Vaqt zonasi: `Asia/Tashkent`.

## Muhim

- `BOT_TOKEN` — BotFather bergan yangi token.
- Bot kanalga administrator qilib qo‘yilgan va “Xabar joylash” huquqiga ega bo‘lishi kerak.
- `GEMINI_API_KEY` bo‘sh qolsa, bot zaxira savollaridan foydalanadi.
- AI orqali yangi savollar yaratish uchun Gemini API kaliti kerak bo‘ladi.

## Ishga tushirish

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python bot.py
```

## Sinov

Botga `/test` yuborilsa, kanalga bitta sinov viktorinasi joylanadi.

## 24/7 server

Loyihani Render, Railway, VPS yoki boshqa doimiy ishlaydigan Python serveriga joylashtiring.
Serverdagi Environment Variables bo‘limiga `.env.example` dagi qiymatlarni kiriting.
