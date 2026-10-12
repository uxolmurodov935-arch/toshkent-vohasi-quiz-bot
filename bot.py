import os
import json
import logging
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes,
    MessageHandler, filters,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
CHANNEL_ID = os.getenv("CHANNEL_ID", "@toshkent_vohasi").strip()
REPO = os.getenv("GITHUB_REPOSITORY", "uxolmurodov935-arch/toshkent-vohasi-quiz-bot").strip()
TZ = ZoneInfo("Asia/Tashkent")
START_DATE = date(2026, 10, 12)
TOTAL_DAYS = 30
TOPICS = [
    "Jadidlar va ma’rifatparvarlar",
    "Mustaqillik tarixi va davlat ramzlari",
    "Tarixiy obidalar va buyuk allomalar",
    "Milliy urf-odatlar, marosimlar va qadriyatlar",
    "Xalq maqollari va milliy meros",
]
ARCHIVE_URL = f"https://raw.githubusercontent.com/{REPO}/main/archive.json"


def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 Viktorinalar arxivi", callback_data="archive:0")],
        [InlineKeyboardButton("📅 Sana bo‘yicha qidirish", callback_data="search:date")],
        [InlineKeyboardButton("🔎 Mavzu bo‘yicha qidirish", callback_data="search:topic")],
        [InlineKeyboardButton("🗓 Kelgusi viktorinalar", callback_data="future:0")],
        [InlineKeyboardButton("ℹ️ Yordam", callback_data="help")],
    ])

async def load_archive():
    # Use GitHub raw file; no extra Python HTTP dependency needed.
    import urllib.request
    try:
        with urllib.request.urlopen(ARCHIVE_URL, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data if isinstance(data, list) else []
    except Exception as exc:
        logging.warning("Arxivni yuklab bo‘lmadi: %s", exc)
        return []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Assalomu alaykum! 📚 Toshkent Vohasi viktorina botiga xush kelibsiz.\n\nKerakli bo‘limni tanlang:",
        reply_markup=main_menu(),
    )

async def show_archive(query, page=0, items=None):
    if items is None:
        items = await load_archive()
    items = sorted(items, key=lambda x: (x.get("date", ""), x.get("time", "")), reverse=True)
    page_size = 5
    selected = items[page*page_size:(page+1)*page_size]
    if not selected:
        text = "📚 Arxiv hozircha bo‘sh. Yangi viktorinalar yuborilgach, ular shu yerda paydo bo‘ladi."
        keyboard = [[InlineKeyboardButton("⬅️ Menyu", callback_data="menu")]]
    else:
        lines = ["📚 **Viktorinalar arxivi**\n"]
        keyboard = []
        for item in selected:
            lines.append(f"• {item.get('date','—')} {item.get('time','')} — {item.get('topic','Viktorina')}\n  {item.get('question','')}")
            if item.get("url"):
                keyboard.append([InlineKeyboardButton("🔗 Ochish: " + item.get("date", "Viktorina"), url=item["url"])])
        nav=[]
        if page > 0: nav.append(InlineKeyboardButton("⬅️ Oldingi", callback_data=f"archive:{page-1}"))
        if (page+1)*page_size < len(items): nav.append(InlineKeyboardButton("Keyingi ➡️", callback_data=f"archive:{page+1}"))
        if nav: keyboard.append(nav)
        keyboard.append([InlineKeyboardButton("⬅️ Menyu", callback_data="menu")])
        text="\n\n".join(lines)
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown", disable_web_page_preview=True)

async def show_future(query, page=0):
    now = datetime.now(TZ)
    entries=[]
    for d in range(TOTAL_DAYS):
        day = START_DATE + timedelta(days=d)
        if day < now.date():
            continue
        for hour in (9, 13, 17):
            dt = datetime(day.year, day.month, day.day, hour, 0, tzinfo=TZ)
            if dt <= now:
                continue
            topic = TOPICS[min((d*3 + (0 if hour==9 else 1 if hour==13 else 2)) // 18, len(TOPICS)-1)]
            entries.append((dt, topic))
    page_size=6
    selected=entries[page*page_size:(page+1)*page_size]
    if not selected:
        text="🗓 Hozircha kelgusi viktorina qolmagan."
        keyboard=[[InlineKeyboardButton("⬅️ Menyu", callback_data="menu")]]
    else:
        text="🗓 **Kelgusi viktorinalar**\n\n" + "\n".join(f"• {dt:%d.%m.%Y %H:%M} — {topic}" for dt,topic in selected)
        nav=[]
        if page>0: nav.append(InlineKeyboardButton("⬅️ Oldingi", callback_data=f"future:{page-1}"))
        if (page+1)*page_size < len(entries): nav.append(InlineKeyboardButton("Keyingi ➡️", callback_data=f"future:{page+1}"))
        keyboard=[nav] if nav else []
        keyboard.append([InlineKeyboardButton("⬅️ Menyu", callback_data="menu")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query=update.callback_query
    await query.answer()
    data=query.data or ""
    if data == "menu":
        await query.edit_message_text("Asosiy menyu. Bo‘limni tanlang:", reply_markup=main_menu())
    elif data.startswith("archive:"):
        await show_archive(query, int(data.split(":")[1]))
    elif data.startswith("future:"):
        await show_future(query, int(data.split(":")[1]))
    elif data == "search:date":
        context.user_data["search_mode"]="date"
        await query.edit_message_text("📅 Sanani DD.MM.YYYY shaklida yuboring. Masalan: 12.10.2026", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Menyu", callback_data="menu")]]))
    elif data == "search:topic":
        rows=[[InlineKeyboardButton(t, callback_data=f"topic:{i}")] for i,t in enumerate(TOPICS)]
        rows.append([InlineKeyboardButton("⬅️ Menyu", callback_data="menu")])
        await query.edit_message_text("🔎 Qaysi mavzudagi viktorinalarni ko‘rmoqchisiz?", reply_markup=InlineKeyboardMarkup(rows))
    elif data.startswith("topic:"):
        topic=TOPICS[int(data.split(":")[1])]
        items=await load_archive()
        matches=[x for x in items if topic.lower() in x.get("topic", "").lower()]
        await show_archive(query, 0, matches)
    elif data == "help":
        await query.edit_message_text("📚 Arxiv — o‘tkazilgan viktorinalar va post havolalari.\n📅 Sana bo‘yicha qidirish uchun DD.MM.YYYY yuboring.\n🔎 Mavzu bo‘yicha qidirish — mavzuni tanlang.\n🗓 Kelgusi viktorinalar — rejalashtirilgan vaqtlar.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Menyu", callback_data="menu")]]))

async def text_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("search_mode") != "date":
        return
    context.user_data.pop("search_mode", None)
    raw=(update.message.text or "").strip()
    try:
        target=datetime.strptime(raw, "%d.%m.%Y").date().isoformat()
    except ValueError:
        await update.message.reply_text("Sana formati noto‘g‘ri. Masalan: 12.10.2026", reply_markup=main_menu())
        return
    items=await load_archive()
    matches=[x for x in items if x.get("date", "") == target]
    if not matches:
        await update.message.reply_text(f"{raw} sanasi uchun arxivda viktorina topilmadi.", reply_markup=main_menu())
        return
    lines=[f"📅 {raw} sanasidagi viktorinalar:\n"]
    buttons=[]
    for item in matches:
        lines.append(f"• {item.get('time','')} — {item.get('topic','Viktorina')}\n{item.get('question','')}")
        if item.get("url"):
            buttons.append([InlineKeyboardButton("🔗 Kanal postini ochish", url=item["url"])])
    buttons.append([InlineKeyboardButton("⬅️ Menyu", callback_data="menu")])
    await update.message.reply_text("\n\n".join(lines), reply_markup=InlineKeyboardMarkup(buttons))

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN muhit o‘zgaruvchisi kiritilmagan.")
    app=Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_search))
    app.run_polling()

if __name__ == "__main__":
    main()
