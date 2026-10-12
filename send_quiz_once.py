import os
import json
import base64
import urllib.request
import urllib.error
from datetime import date, datetime
from zoneinfo import ZoneInfo
from telegram import Bot
from quiz_savollar_30_kun import QUESTIONS

CHANNEL = "@toshkent_vohasi"
TASHKENT = ZoneInfo("Asia/Tashkent")
START_DATE = date(2026, 10, 12)
TOTAL_DAYS = 30
REPO = os.getenv("GITHUB_REPOSITORY", "uxolmurodov935-arch/toshkent-vohasi-quiz-bot")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
TOPICS = [
    "Jadidlar va ma’rifatparvarlar",
    "Mustaqillik tarixi va davlat ramzlari",
    "Tarixiy obidalar va buyuk allomalar",
    "Milliy urf-odatlar, marosimlar va qadriyatlar",
    "Xalq maqollari va milliy meros",
]
CRON_SLOTS = {"0 4 * * *": 0, "0 8 * * *": 1, "0 12 * * *": 2}


def topic_for(index):
    return TOPICS[min(index // 18, len(TOPICS)-1)]


def github_request(url, method="GET", payload=None):
    headers={"Accept":"application/vnd.github+json", "User-Agent":"toshkent-vohasi-quiz-bot"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    data=json.dumps(payload).encode() if payload is not None else None
    req=urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=20) as r:
        body=r.read().decode()
        return json.loads(body) if body else {}


def save_archive(entry):
    if not GITHUB_TOKEN:
        print("GITHUB_TOKEN yo‘q: viktorina yuboriladi, lekin arxiv GitHub’ga saqlanmaydi.")
        return
    url=f"https://api.github.com/repos/{REPO}/contents/archive.json"
    try:
        try:
            existing=github_request(url)
            sha=existing.get("sha")
            content=base64.b64decode(existing.get("content", "")).decode("utf-8")
            archive=json.loads(content) if content.strip() else []
        except urllib.error.HTTPError as e:
            if e.code != 404: raise
            sha=None; archive=[]
        archive=[x for x in archive if x.get("message_id") != entry.get("message_id")]
        archive.append(entry)
        payload={"message":f"Add quiz archive entry {entry['date']} {entry['time']}",
                 "content":base64.b64encode(json.dumps(archive, ensure_ascii=False, indent=2).encode()).decode()}
        if sha: payload["sha"]=sha
        github_request(url, "PUT", payload)
        print("Viktorina arxivga saqlandi.")
    except Exception as e:
        print(f"Arxivni saqlashda xatolik: {e}")


async def main():
    token=os.getenv("BOT_TOKEN")
    if not token: raise ValueError("BOT_TOKEN topilmadi!")
    now=datetime.now(TASHKENT)
    day_number=(now.date()-START_DATE).days+1
    if not 1 <= day_number <= TOTAL_DAYS:
        print("Quiz muddati tugagan yoki hali boshlanmagan."); return
    schedule=os.getenv("SCHEDULE_CRON", "")
    if schedule in CRON_SLOTS:
        slot=CRON_SLOTS[schedule]
    else:
        manual={9:0,13:1,17:2}
        if now.hour not in manual:
            print(f"Hozir {now:%H:%M}. Qo‘lda sinash uchun 09:00, 13:00 yoki 17:00 da ishga tushiring."); return
        slot=manual[now.hour]
    index=(day_number-1)*3+slot
    if index >= len(QUESTIONS): raise ValueError("Savollar soni 90 tadan kam.")
    q=QUESTIONS[index]
    correct=int(q["correct_option_id"])
    options=q["options"]
    explanation=q.get("explanation", f"To‘g‘ri javob: {options[correct]}")[:200]
    bot=Bot(token)
    message=await bot.send_poll(chat_id=CHANNEL, question=q["question"], options=options,
        type="quiz", correct_option_id=correct, is_anonymous=True, explanation=explanation)
    post_url=f"https://t.me/{CHANNEL.lstrip('@')}/{message.message_id}"
    entry={"date":now.date().isoformat(),"time":now.strftime("%H:%M"),"topic":topic_for(index),
           "question":q["question"],"url":post_url,"message_id":message.message_id,
           "day":day_number,"slot":slot+1}
    save_archive(entry)
    print(f"Quiz yuborildi: {entry['date']} {entry['time']} | {day_number}-kun | {slot+1}-viktorina")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
