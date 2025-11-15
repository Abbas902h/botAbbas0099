import sqlite3
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ✅ تشغيل مستمر لمنع توقف البوت
from keep_alive import keep_alive
keep_alive()

BOT_TOKEN = "8599216793:AAEC-SXCW-jJCTzFNWgz67rHSe9-hiWhkv0"
CHANNEL_ID = -1003464951799
ADMIN_ID = 6494650596

# ✅ قاعدة بيانات الأفلام
def init_db():
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS movies (name TEXT PRIMARY KEY, message_id INTEGER)")
    conn.commit()
    conn.close()

def add_movie(name, message_id):
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    cursor.execute("REPLACE INTO movies (name, message_id) VALUES (?, ?)", (name, message_id))
    conn.commit()
    conn.close()

def delete_movie(name):
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM movies WHERE name = ?", (name,))
    conn.commit()
    deleted = cursor.rowcount
    conn.close()
    return deleted > 0

def get_message_id(name):
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    cursor.execute("SELECT message_id FROM movies WHERE name = ?", (name,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def save_user_id(user_id):
    try:
        with open("users.txt", "r") as f:
            users = f.read().splitlines()
    except FileNotFoundError:
        users = []

    if str(user_id) not in users:
        with open("users.txt", "a") as f:
            f.write(f"{user_id}\n")

# ✅ إدارة قنوات الاشتراك الإجباري
def load_channels():
    try:
        with open("channels.txt", "r") as f:
            return f.read().splitlines()
    except FileNotFoundError:
        return []

def save_channel(username):
    channels = load_channels()
    if username not in channels:
        with open("channels.txt", "a") as f:
            f.write(f"{username}\n")
        return "✅ تم إضافة القناة"
    else:
        channels.remove(username)
        with open("channels.txt", "w") as f:
            for ch in channels:
                f.write(f"{ch}\n")
        return "✅ تم حذف القناة"

# ✅ التحقق من الاشتراك
async def check_subscription(user_id, context):
    if user_id == ADMIN_ID:
        return True

    channels = load_channels()
    for ch in channels:
        try:
            member = await context.bot.get_chat_member(chat_id=ch, user_id=user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

# ✅ أمر /start للتحقق من الاشتراك
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 🌟 التعديل 1: التحقق من وجود المستخدم الفعال 🌟
    if update.effective_user is None:
        return

    user_id = update.effective_user.id
    save_user_id(user_id)

    await asyncio.sleep(0.5)

    if not await check_subscription(user_id, context):
        channels = load_channels()
        msg = "❌ اشترك في القنوات التالية لاستخدام البوت ثم اضغط /start:\n"
        for ch in channels:
            msg += f"👉 {ch}\n"
        await update.message.reply_text(msg)
        return

    await update.message.reply_text("✅ مرحبًا بك! يمكنك الآن استخدام البوت بحرية.")

# ✅ أمر /chn لإضافة أو حذف قناة
async def chn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 🌟 التعديل 2: التحقق من وجود المستخدم الفعال 🌟
    if update.effective_user is None:
        return

    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ هذا الأمر مخصص للإدمن فقط.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("❌ استخدم الأمر هكذا: /chn @username")
        return

    username = context.args[0]
    result = save_channel(username)
    await update.message.reply_text(result)

# ✅ أمر /add لإضافة فيلم
async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 🌟 التعديل 3: التحقق من وجود المستخدم الفعال 🌟
    if update.effective_user is None:
        return

    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ هذا الأمر مخصص للإدمن فقط.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("❌ استخدم الأمر هكذا: /add اسم_الفيلم رقم_الرسالة")
        return

    name = " ".join(context.args[:-1])
    try:
        message_id = int(context.args[-1])
        add_movie(name, message_id)
        await update.message.reply_text(f"✅ تم إضافة الفيلم: {name}")
    except ValueError:
        await update.message.reply_text("❌ رقم الرسالة غير صحيح")

# ✅ أمر /dis لحذف فيلم
async def dis_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 🌟 التعديل 4: التحقق من وجود المستخدم الفعال 🌟
    if update.effective_user is None:
        return

    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ هذا الأمر مخصص للإدمن فقط.")
        return

    if len(context.args) < 1:
        await update.message.reply_text("❌ استخدم الأمر هكذا: /dis اسم_الفيلم")
        return

    name = " ".join(context.args)
    if delete_movie(name):
        await update.message.reply_text(f"✅ تم حذف الفيلم: {name}")
    else:
        await update.message.reply_text("❌ هذا الفيلم غير موجود في قاعدة البيانات.")

# ✅ أمر /sher للنشر العام مع تأخير
async def sher_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 🌟 التعديل 5: التحقق من وجود المستخدم الفعال 🌟
    if update.effective_user is None:
        return

    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ هذا الأمر مخصص للإدمن فقط.")
        return

    if len(context.args) < 1:
        await update.message.reply_text("❌ استخدم الأمر هكذا: /sher رسالتك هنا")
        return

    message = " ".join(context.args)

    try:
        with open("users.txt", "r") as f:
            user_ids = f.read().splitlines()
    except FileNotFoundError:
        user_ids = []

    count = 0
    for uid in user_ids:
        try:
            await context.bot.send_message(chat_id=int(uid), text=message)
            count += 1
            await asyncio.sleep(0.05)
        except:
            pass

    await update.message.reply_text(f"✅ تم إرسال الرسالة إلى {count} مستخدم.")

# ✅ التعامل مع الرسائل
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 🌟 التعديل 6: التحقق من وجود المستخدم الفعال (الأهم) 🌟
    if update.effective_user is None:
        return

    user_id = update.effective_user.id
    save_user_id(user_id)

    if not await check_subscription(user_id, context):
        channels = load_channels()
        msg = "❌ اشترك في القنوات التالية لاستخدام البوت ثم اضغط /start:\n"
        for ch in channels:
            msg += f"👉 {ch}\n"
        await update.message.reply_text(msg)
        return

    name = update.message.text.strip()
    message_id = get_message_id(name)
    chat_id = update.effective_chat.id

    if message_id:
        sent = await context.bot.forward_message(chat_id=chat_id, from_chat_id=CHANNEL_ID, message_id=message_id)

        async def delete_later():
            await asyncio.sleep(15)
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=sent.message_id)
            except:
                pass

        asyncio.create_task(delete_later())
    else:
        await update.message.reply_text("❌ الفيلم غير موجود في قاعدة البيانات")

# ✅ تشغيل البوت
init_db()
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start_command))
app.add_handler(CommandHandler("add", add_command))
app.add_handler(CommandHandler("dis", dis_command))
app.add_handler(CommandHandler("sher", sher_command))
app.add_handler(CommandHandler("chn", chn_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()
