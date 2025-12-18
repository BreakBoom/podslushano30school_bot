import os
import time
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

TOKEN = os.getenv("8379070931:AAFvo5KxQoqDQLTd97dE1z2szmTG6UlDW3w")
CHANNEL_ID = int(os.getenv("-1003522672383"))
BOT_USERNAME = os.getenv("@podslushano30school_bot")
CHANNEL_LINK = os.getenv("https://t.me/+ZkN-Gu6dXfIyMGEy")
CHAT_LINK = os.getenv("https://t.me/+AswNm3B1qOkxMGZi")

# ===== ДАННЫЕ =====
admins = set()
banned = set()
last_message_time = {}
stats = {"total": 0, "published": 0, "rejected": 0}
post_counter = 0

BAD_WORDS = ["убью", "сука", "пизд", "хуй", "блять"]

# ===== УТИЛИТЫ =====
def is_admin(user_id: int):
    return user_id in admins

def has_bad_words(text: str):
    return any(w in text.lower() for w in BAD_WORDS)

# ===== /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🕵️ Подслушано 30 школа\n\n"
        "Присылай анонимные сплетни и истории.\n"
        "⏱️ Ограничение: 1 сообщение в минуту.\n\n"
        f"📢 Канал: {CHANNEL_LINK}\n"
        f"💬 Чат: {CHAT_LINK}"
    )

# ===== ПОЛЬЗОВАТЕЛЬСКИЕ СООБЩЕНИЯ =====
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    now = time.time()

    if user_id in banned:
        return

    if user_id in last_message_time and now - last_message_time[user_id] < 60:
        await update.message.reply_text(
            "⏳ Сработал антиспам.\nМожно отправлять 1 сообщение в минуту."
        )
        return

    last_message_time[user_id] = now
    stats["total"] += 1
    text = update.message.text

    warning = " ⚠️ Обнаружены запрещённые слова" if has_bad_words(text) else ""

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Опубликовать", callback_data=f"pub|{text}"),
        InlineKeyboardButton("❌ Отклонить", callback_data="rej")
    ]])

    for admin_id in admins:
        await context.bot.send_message(
            admin_id,
            f"📩 Новое анонимное сообщение:{warning}\n\n{text}",
            reply_markup=keyboard
        )

    await update.message.reply_text(
        "✅ Анонимное сообщение отправлено.\n"
        f"📢 Канал: {CHANNEL_LINK}\n"
        f"💬 Чат: {CHAT_LINK}"
    )

# ===== МОДЕРАЦИЯ =====
async def moderation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global post_counter
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        return

    action, *data = query.data.split("|")

    if action == "pub":
        post_counter += 1
        stats["published"] += 1
        text = data[0]

        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "✉️ Оставить анонимное сообщение",
                url=f"https://t.me/{BOT_USERNAME}"
            )
        ]])

        await context.bot.send_message(
            CHANNEL_ID,
            f"🕵️ Подслушано №{post_counter}\n\n{text}\n\n#подслушано30",
            reply_markup=keyboard
        )
        await query.edit_message_text("✅ Опубликовано")

    elif action == "rej":
        stats["rejected"] += 1
        await query.edit_message_text("❌ Отклонено")

# ===== АДМИН-ПАНЕЛЬ =====
async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.message.from_user.id):
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Статистика", callback_data="panel_stats")],
        [InlineKeyboardButton("👥 Администраторы", callback_data="panel_admins")],
        [InlineKeyboardButton("🚫 Заблокированные", callback_data="panel_banned")],
        [InlineKeyboardButton("⚙️ Настройки", callback_data="panel_settings")],
        [InlineKeyboardButton("❌ Закрыть", callback_data="panel_close")]
    ])

    await update.message.reply_text("🛡️ Админ-панель", reply_markup=keyboard)

async def panel_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        return

    data = query.data

    if data == "panel_stats":
        await query.edit_message_text(
            f"📊 Статистика:\n"
            f"Всего: {stats['total']}\n"
            f"Опубликовано: {stats['published']}\n"
            f"Отклонено: {stats['rejected']}"
        )

    elif data == "panel_admins":
        await query.edit_message_text(
            "👥 Администраторы:\n" +
            "\n".join(map(str, admins)) +
            "\n\n➕ /addadmin ID\n➖ /deladmin ID"
        )

    elif data == "panel_banned":
        await query.edit_message_text(
            "🚫 Заблокированные:\n" +
            ("\n".join(map(str, banned)) if banned else "Пусто")
        )

    elif data == "panel_settings":
        await query.edit_message_text(
            "⚙️ Настройки:\n"
            "Антиспам: 1 сообщение в минуту"
        )

    elif data == "panel_close":
        await query.edit_message_text("Админ-панель закрыта")

# ===== КОМАНДЫ АДМИНА =====
async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_admin(update.message.from_user.id):
        admins.add(int(context.args[0]))
        await update.message.reply_text("✅ Администратор добавлен")

async def del_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_admin(update.message.from_user.id):
        admins.discard(int(context.args[0]))
        await update.message.reply_text("🗑️ Администратор удалён")

# ===== ЗАПУСК =====
app = ApplicationBuilder().token(TOKEN).build()
admins.add(int(os.getenv("ADMIN_ID")))

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("panel", panel))
app.add_handler(CommandHandler("addadmin", add_admin))
app.add_handler(CommandHandler("deladmin", del_admin))

app.add_handler(CallbackQueryHandler(panel_actions, pattern="panel_"))
app.add_handler(CallbackQueryHandler(moderation))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()
