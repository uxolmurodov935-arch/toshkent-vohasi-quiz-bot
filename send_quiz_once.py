
import os
from datetime import date, datetime
from zoneinfo import ZoneInfo

from telegram import Bot
from quiz_savollar_30_kun import QUESTIONS

CHANNEL = "@toshkent_vohasi"
TASHKENT = ZoneInfo("Asia/Tashkent")

START_DATE = date(2026, 10, 12)
TOTAL_DAYS = 30

# GitHub Actions jadvali: UTC -> Toshkent vaqti
CRON_SLOTS = {
    "0 4 * * *": 0,   # 09:00
    "0 8 * * *": 1,   # 13:00
    "0 12 * * *": 2,  # 17:00
}


async def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN topilmadi!")

    now = datetime.now(TASHKENT)
    day_number = (now.date() - START_DATE).days + 1

    if not 1 <= day_number <= TOTAL_DAYS:
        print("Quiz muddati tugagan yoki hali boshlanmagan.")
        return

    schedule = os.environ.get("SCHEDULE_CRON")

    if schedule in CRON_SLOTS:
        slot = CRON_SLOTS[schedule]
        print(f"Avtomatik jadval: {schedule}")
    else:
        # Qo'lda ishga tushirganda faqat belgilangan soatlarda yuboradi
        manual_slots = {
            9: 0,
            13: 1,
            17: 2,
        }

        if now.hour not in manual_slots:
            print(
                f"Hozirgi vaqt {now.strftime('%H:%M')}. "
                "Qo'lda yuborish uchun 09:00, 13:00 yoki 17:00 da ishga tushiring."
            )
            return

        slot = manual_slots[now.hour]
        print("Qo'lda ishga tushirildi.")

    # Har kun uchun ketma-ket 3 ta savol
    question_index = (day_number - 1) * 3 + slot

    if question_index >= len(QUESTIONS):
        print("Savollar tugagan.")
        return

    q = QUESTIONS[question_index]
    correct_id = q["correct_option_id"]
    options = q["options"]

    if not 0 <= correct_id < len(options):
        raise ValueError(f"{question_index + 1}-savolda javob indeksi xato.")

    explanation = q.get(
        "explanation",
        f"To'g'ri javob: {options[correct_id]}."
    )[:200]

    bot = Bot(token=token)
    await bot.send_poll(
        chat_id=CHANNEL,
        question=q["question"],
        options=options,
        type="quiz",
        correct_option_id=correct_id,
        is_anonymous=True,
        explanation=explanation,
    )

    print(
        f"Quiz yuborildi: {now:%Y-%m-%d %H:%M} | "
        f"{day_number}-kun | {slot + 1}-viktorina"
    )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
