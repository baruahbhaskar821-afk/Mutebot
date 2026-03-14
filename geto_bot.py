
import json
import asyncio
import time
import random
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

# ================= CONFIG =================
BOT_TOKEN = "PASTE_YOUR_BOT_TOKEN_HERE"
OWNER_ID = 7616709190
DATA_FILE = "data.json"

SPEED_DELAY = 0.001
EVERYONE_DELAY = 1.2
EVERYONE_BATCH = 5
MAX_STICKER = 100
MAX_SPAM = 20
SPAM_DELAY = 0.4

# ================= LOGGING =================
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
    handlers=[logging.FileHandler("geto.log"), logging.StreamHandler()]
)
log = logging.getLogger("GETO")

SPAM_RUNNING = {}

# ================= DATA =================
def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        data = {
            "sudo_users": [],
            "mute_delete": [],
            "tmute": {},
            "stickers": [],
            "shayari": {
                "love": [],
                "sad": [],
                "birthday": []
            }
        }
        save_data(data)
        return data

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def is_owner(uid):
    return uid == OWNER_ID

def is_sudo(uid, data):
    return uid == OWNER_ID or uid in data.get("sudo_users", [])

def get_mention(user):
    if user.username:
        return f"@{user.username}"
    return f'<a href="tg://user?id={user.id}">{user.first_name}</a>'

async def auto_delete(update, context, data):
    msg = update.message
    if not msg or not msg.from_user:
        return False

    uid = msg.from_user.id

    if is_sudo(uid, data):
        return False

    if uid in data["mute_delete"]:
        try:
            await msg.delete()
            return True
        except:
            pass

    if uid in data["tmute"]:
        if time.time() < data["tmute"][uid]:
            try:
                await msg.delete()
                return True
            except:
                pass
        else:
            data["tmute"].pop(uid, None)
            save_data(data)

    return False

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    data = load_data()
    uid = msg.from_user.id if msg.from_user else None
    chat_id = msg.chat.id
    txt = (msg.text or "").strip().lower()
    target = msg.reply_to_message.from_user if msg.reply_to_message else None

    if uid and await auto_delete(update, context, data):
        return

    if txt == ".alive":
        await msg.reply_text("Bot Online ✅")
        return

    if txt in [".ping", ".speed"]:
        start = time.time()
        m = await msg.reply_text("Calculating...")
        ping = int((time.time() - start) * 1000)
        await m.edit_text(f"PONG: {ping} ms")
        return

    if txt.startswith(".") and uid and not is_sudo(uid, data):
        await msg.reply_text("Sudo required!")
        return

    if txt.startswith(".spam ") and uid and is_sudo(uid, data):
        try:
            parts = txt.split(maxsplit=2)
            count = int(parts[1])
            spam_text = parts[2]

            for _ in range(count):
                await context.bot.send_message(chat_id, spam_text)
                await asyncio.sleep(SPAM_DELAY)
        except:
            await msg.reply_text("Usage: .spam 5 hello")
        return

    if txt == ".mute" and target and uid and is_sudo(uid, data):
        if target.id not in data["mute_delete"]:
            data["mute_delete"].append(target.id)
            save_data(data)
        await msg.reply_text("User muted")
        return

    if txt == ".unmute" and target and uid and is_sudo(uid, data):
        if target.id in data["mute_delete"]:
            data["mute_delete"].remove(target.id)
            save_data(data)
        await msg.reply_text("User unmuted")
        return

# ================= MAIN =================
def main():
    print("GETO BOT STARTED")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handler))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
