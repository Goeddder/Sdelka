import asyncio
import random
from datetime import datetime, time, timedelta
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatAction, ParseMode

# --- НАЛАШТУВАННЯ ---
API_ID = 33949991
API_HASH = "1b75c81111e993ec9ecd7035e7f572a8"
BOT_TOKEN = "8521570475:AAFt3MbZIoU_qvwFRaQnRbcuCUs7TobXgXU"
STRING_SESSION = "AgIGCScAKkLcFE9QvCZ7CJeqkoqFzSRvgBZ0htSUCEVvHcjApfAIbFXCnJ_DhhHKCfY57a0h4FmkmuVVfYBxgBveq-Xp6YwjJPjL0oPg5hhHnczcs8W33mFOxl8H8ZQIQwrflfgzO608ZpyC_LfUbh8msSOSpud_MkDME8Y2cdzKStlOIfgLboz-rYHr4zf5EsOSKvsUiwT21H-OoDS0YEMcH3xASjQIFLoz0P8vh7N6O6x6wpHJ8FAxdQ9bTakS-Lp4NHk9jLwCp9PWIl_-0zRttWVYpNC-kTG23_OvSEXKk4bHhb6Ofb2gUHLXniDYWybFqeZAGeCpNswFPkKXIDxdVOQmMAAAAABXsl0xAA"

# Список цілей (ID користувачів)
TARGET_IDS = [839209146, 59991523, 2025257353]
REPLY_VARIANTS = ["Го", "я", "в лс", "Я проведу", "Го я", "Пиши", "Я"]

# Параметри модулів
NIGHT_START = time(0, 0)
NIGHT_END = time(7, 0)
COOLDOWN_MIN = 5

# Ініціалізація клієнтів
bot = Client("manager_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user = Client("my_account", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)

# Глобальний стан
state = {
    "active": False,
    "total": 0,
    "my_id": None,
    "cooldowns": {},
    "start_time": datetime.now().strftime("%d.%m %H:%M")
}

# --- ГЕНЕРАЦІЯ МЕНЮ ---
def get_main_menu():
    status_icon = "🟢 АКТИВНИЙ" if state["active"] else "🔴 ВИМКНЕНИЙ"
    text = (
        f"<b>🚀 ULTRA CLOUD MANAGER v4.5</b>\n"
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"<b>Статус:</b> {status_icon}\n"
        f"<b>Угод за сесію:</b> <code>{state['total']}</code>\n"
        f"<b>Цілей у списку:</b> <code>{len(TARGET_IDS)}</code>\n"
        f"<b>Запущено на Railway:</b> <code>{state['start_time']}</code>\n"
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"<i>Керуй кнопками або командою .сделка</i>"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ УВІМКНУТИ", callback_data="p_on"), 
         InlineKeyboardButton("❌ ВИМКНУТИ", callback_data="p_off")],
        [InlineKeyboardButton("📊 ОНОВИТИ ДАНІ", callback_data="p_refresh")]
    ])
    return text, kb

# --- ОБРОБКА КНОПОК (FIXED FOR RAILWAY) ---
@bot.on_callback_query()
async def cb_handler(c, q):
    global state
    try:
        if q.data == "p_on":
            state["active"] = True
        elif q.data == "p_off":
            state["active"] = False
        
        text, kb = get_main_menu()
        await q.edit_message_text(text, reply_markup=kb)
        await q.answer("Статус оновлено!")
    except Exception as e:
        print(f"Помилка кнопок: {e}")

# --- КОМАНДИ МЕНЕДЖЕР-БОТА ---
@bot.on_message(filters.command("start") & filters.private)
async def bot_start_cmd(c, m):
    text, kb = get_main_menu()
    await m.reply(text, reply_markup=kb)

# --- КОМАНДИ ЮЗЕР-БОТА (З ВИДАЛЕННЯМ) ---
@user.on_message(filters.me & filters.text)
async def user_commands(c, m):
    global state
    cmd = m.text.lower()
    
    if cmd == ".сделка старт":
        state["active"] = True
        await m.edit("🚀 <b>Ловець активований!</b>")
        await asyncio.sleep(2)
        await m.delete()
    elif cmd == ".сделка стоп":
        state["active"] = False
        await m.edit("😴 <b>Ловець зупинений.</b>")
        await asyncio.sleep(2)
        await m.delete()
    elif cmd == ".сделка":
        text, kb = get_main_menu()
        if state["my_id"]:
            await bot.send_message(state["my_id"], text, reply_markup=kb)
            await m.edit("📟 <b>Меню надіслано в Менеджер-бот</b>")
            await asyncio.sleep(2)
            await m.delete()

# --- ОСНОВНИЙ МОДУЛЬ ПЕРЕХОПЛЕННЯ ---
@user.on_message(filters.text & ~filters.me & ~filters.bot)
async def message_hunter(c, m):
    global state
    if not state["active"] or not m.from_user or m.from_user.id not in TARGET_IDS:
        return

    # Перевірка нічного режиму
    now_time = datetime.now().time()
    if NIGHT_START <= now_time <= NIGHT_END:
        return

    # Анти-флуд
    uid = m.from_user.id
    if uid in state["cooldowns"]:
        if datetime.now() < state["cooldowns"][uid]:
            return

    original_text = (m.text or "").strip()
    text_lower = original_text.lower()

    if "#сделка" in text_lower:
        # Ігнор валюти
        if any(x in text_lower for x in ["руб", "₽", "rub"]):
            return
        
        # Перевірка на зміст (не пустий тег)
        clean = original_text.replace("#сделка", "").replace("#Сделка", "").strip()
        if not clean:
            return

        try:
            # Рандомна затримка (читання + друк)
            await asyncio.sleep(random.uniform(2.5, 5.0))
            await c.send_chat_action(m.chat.id, ChatAction.TYPING)
            await asyncio.sleep(random.uniform(1.0, 2.0))

            # Вибір відповіді
            ans = f"{random.choice(REPLY_VARIANTS)} {random.choice(EMOJIS)}".strip()
            if random.choice([True, False]):
                ans = ans.lower()
            
            # Відправка відповіді (ЗАЛИШАЄТЬСЯ В ЧАТІ)
            await m.reply(ans)
            
            # Оновлення статистики та кулдауну
            state["total"] += 1
            state["cooldowns"][uid] = datetime.now() + timedelta(minutes=COOLDOWN_MIN)

            # Надсилання звіту в менеджер-бот
            if state["my_id"]:
                report = (
                    f"🎯 <b>ПЕРЕХОПЛЕННЯ!</b>\n"
                    f"👤 <b>Від:</b> <code>{uid}</code>\n"
                    f"💬 <b>Текст:</b> <i>{original_text[:100]}</i>\n"
                    f"🔗 <a href='{m.link}'>ПЕРЕЙТИ ДО ЧАТУ</a>"
                )
                await bot.send_message(state["my_id"], report, disable_web_page_preview=True)
                
        except Exception as e:
            print(f"Помилка перехоплення: {e}")

# --- ЗАПУСК СИСТЕМИ ---
async def main_runner():
    print("⏳ Підключення до Telegram Cloud...")
    try:
        await bot.start()
        await user.start()
        me = await user.get_me()
        state["my_id"] = me.id
        print(f"✅ УСПІШНО! Бот: @{me.username if me.username else me.first_name}")
        print("🚀 СИСТЕМА ПРАЦЮЄ 24/7 НА RAILWAY")
        await idle()
    except Exception as e:
        print(f"❌ КРИТИЧНА ПОМИЛКА ЗАПУСКУ: {e}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main_runner())
    
