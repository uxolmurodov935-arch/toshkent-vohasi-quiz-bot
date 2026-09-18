import os
import json
import random
import logging
from datetime import time
from zoneinfo import ZoneInfo

import aiohttp
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
CHANNEL_ID = os.getenv("CHANNEL_ID", "@toshkent_vohasi").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
TZ = ZoneInfo("Asia/Tashkent")

TOPICS = [
    "Ma’naviyat va ma’rifat",
    "Tarix",
    "Umumiy bilim",
    "Milliy qadriyatlar",
]

FALLBACK_QUESTIONS = [
    {
        "topic": "Tarix",
        "question": "O‘zbekiston Respublikasi Konstitutsiyasi qachon qabul qilingan?",
        "options": ["1991-yil 31-avgust", "1992-yil 8-dekabr", "1993-yil 1-sentabr", "1995-yil 9-may"],
        "correct": 1,
        "explanation": "O‘zbekiston Respublikasi Konstitutsiyasi 1992-yil 8-dekabrda qabul qilingan."
    },
    {
        "topic": "Milliy qadriyatlar",
        "question": "Navro‘z bayrami odatda qaysi sanada nishonlanadi?",
        "options": ["1-yanvar", "8-mart", "21-mart", "9-may"],
        "correct": 2,
        "explanation": "Navro‘z bahorgi tengkunlik — 21-mart kuni nishonlanadi."
    },
    {
        "topic": "Umumiy bilim",
        "question": "Yerning tabiiy yo‘ldoshi nima?",
        "options": ["Quyosh", "Oy", "Mars", "Venera"],
        "correct": 1,
        "explanation": "Oyning o‘zi emas, Yerning tabiiy yo‘ldoshi — Oy hisoblanadi."
    },
    {
        "topic": "Ma’naviyat va ma’rifat",
        "question": "Kitob mutolaasi insonda, avvalo, nimani rivojlantiradi?",
        "options": ["Bilim va tafakkurni", "Faqat jismoniy kuchni", "Uyquni", "Tez yugurishni"],
        "correct": 0,
        "explanation": "Mutolaa bilimni, dunyoqarashni, tafakkur va nutq boyligini rivojlantirishga yordam beradi."
    },
]

async def generate_with_gemini():
    prompt = f"""
O‘zbek tilida bitta sifatli viktorina savoli tuz.
Mavzu: {random.choice(TOPICS)}
Savol aniq va faktlarga asoslangan bo‘lsin.
4 ta javob varianti bo‘lsin, faqat bittasi to‘g‘ri.
Quyidagi JSON formatidan qat’iy foydalan:
{{
  "topic": "mavzu",
  "question": "savol",
  "options": ["A", "B", "C", "D"],
  "correct": 0,
  "explanation": "1-2 jumlalik izoh"
}}
"correct" 0 dan 3 gacha bo‘lgan indeks bo‘lsin. Hech qanday qo‘shimcha matn yozma.
"""
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    )
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url,
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=45,
        ) as response:
            response.raise_for_status()
            data = await response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            text = text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)

async def get_question():
    if GEMINI_API_KEY:
        try:
            question = await generate_with_gemini()
            if (
                isinstance(question, dict)
                and len(question.get("options", [])) == 4
                and 0 <= int(question.get("correct", -1)) <= 3
            ):
                return question
        except Exception:
            logging.exception("AI savol yaratishda xatolik; zaxira savol ishlatiladi.")
    return random.choice(FALLBACK_QUESTIONS)

async def post_quiz(context: ContextTypes.DEFAULT_TYPE):
    q = await get_question()
    explanation = q.get("explanation", "")
    correct = int(q["correct"])
    question_text = f"🧠 BUGUNGI VIKTORINA\n\n📚 Mavzu: {q.get('topic', 'Umumiy bilim')}\n\n❓ {q['question']}"
    message = await context.bot.send_poll(
        chat_id=CHANNEL_ID,
        question=question_text,
        options=q["options"],
        type="quiz",
        correct_option_id=correct,
        is_anonymous=True,
        explanation=explanation[:200],
    )
    logging.info("Viktorina joylandi: %s", message.message_id)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bot ishlayapti. Har kuni 09:00, 11:00, 14:00, 16:00 va 18:00 da viktorina joylanadi."
    )

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await post_quiz(context)
    await update.message.reply_text("Sinov viktorinasi kanalga joylandi.")

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN muhit o‘zgaruvchisi kiritilmagan.")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test))

    # Asia/Tashkent vaqtida har kuni 5 ta post
    for hour in [9, 11, 14, 16, 18]:
        app.job_queue.run_daily(
            post_quiz,
            time=time(hour=hour, minute=0, tzinfo=TZ),
            name=f"quiz_{hour}",
        )

    app.run_polling()

if __name__ == "__main__":
    main()
