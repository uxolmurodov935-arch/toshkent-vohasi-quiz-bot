import os
from datetime import date, datetime
from zoneinfo import ZoneInfo

from telegram import Bot
from quiz_savollar_17_kun import QUESTIONS

CHANNEL = "@toshkent_vohasi"
TASHKENT = ZoneInfo("Asia/Tashkent")

START_DATE = date(2026, 10, 6)
TOTAL_DAYS = 17

# GitHub Actions cron -> quiz slot
CRON_SLOTS = {
    "7 4 * * *": 0,   # 09:07 Toshkent
    "7 6 * * *": 1,   # 11:07 Toshkent
    "7 9 * * *": 2,   # 14:07 Toshkent
    "7 11 * * *": 3,  # 16:07 Toshkent
    "7 13 * * *": 4,  # 18:07 Toshkent
}


async def main():
    token = os.environ.get("BOT_TOKEN")

    if not token:
        raise ValueError("BOT_TOKEN topilmadi!")

    now = datetime.now(TASHKENT)

    day_number = (now.date() - START_DATE).days + 1

    if day_number < 1 or day_number > TOTAL_DAYS:
        print("Quiz muddati tugagan yoki hali boshlanmagan.")
        return

    # GitHub Actions qaysi cron orqali ishga tushganini aniqlash
    schedule = os.environ.get("SCHEDULE_CRON")

    if schedule in CRON_SLOTS:
        slot = CRON_SLOTS[schedule]
        print(f"Avtomatik schedule aniqlandi: {schedule}")
    else:
        # Qo'lda Run workflow bosilganda
        manual_slots = {
            9: 0,
            11: 1,
            14: 2,
            16: 3,
            18: 4,
        }

        if now.hour not in manual_slots:
            print(
                f"Hozirgi vaqt: {now.strftime('%H:%M')}. "
                "Quiz vaqti emas."
            )
            return

        slot = manual_slots[now.hour]
        print("Qo'lda ishga tushirildi.")

    question_index = (day_number - 1) * 5 + slot

    if question_index >= len(QUESTIONS):
        print("Savollar tugagan.")
        return

    q = QUESTIONS[question_index]

    bot = Bot(token=token)

    await bot.send_poll(
        chat_id=CHANNEL,
        question=q["question"],
        options=q["options"],
        type="quiz",
        correct_option_id=q["correct_option_id"],
        is_anonymous=True,
    )

    print(
        f"Quiz yuborildi: "
        f"{now.strftime('%Y-%m-%d %H:%M')} | "
        f"{day_number}-kun | "
        f"{slot + 1}-slot"
    )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
