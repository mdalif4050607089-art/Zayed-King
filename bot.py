import base64
import os
from pyrogram import Client, filters
from pyrogram.types import Message

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID"))
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

app = Client(
    "private_video_link_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True,
)


def encode_msg_id(msg_id: int) -> str:
    raw = f"vid:{msg_id}".encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def decode_token(token: str) -> int | None:
    try:
        padded = token + "=" * ((4 - len(token) % 4) % 4)
        decoded = base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8")
        if decoded.startswith("vid:"):
            return int(decoded.split(":", 1)[1])
    except Exception:
        return None
    return None


@app.on_message(filters.private & filters.command("start"))
async def start_handler(client: Client, message: Message):
    user = message.from_user
    if not user:
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) == 1:
        await message.reply_text(
            "স্বাগতম! আপনার ভিডিও লিংক থাকলে সেটি দিয়ে বটে প্রবেশ করুন অথবা নিচে আপনার টোকেন পাঠান।"
        )
        return

    token = parts[1].strip()
    msg_id = decode_token(token)
    if not msg_id:
        await message.reply_text("❌ টোকেনটি সঠিক নয় বা মেয়াদোত্তীর্ণ।")
        return

    try:
        await client.copy_message(
            chat_id=message.chat.id,
            from_chat_id=CHANNEL_ID,
            message_id=msg_id,
        )
    except Exception:
        await message.reply_text(
            "⚠️ প্রাইভেট চ্যানেল থেকে ভিডিওটি পাঠানো যাচ্ছে না। চ্যানেলে ভিডিওটি আছে কি না বা বট অ্যাডমিন আছে কি না যাচাই করুন।"
        )


@app.on_message(filters.private & filters.video)
async def save_video_handler(client: Client, message: Message):
    user = message.from_user
    if not user or user.id != ADMIN_ID:
        await message.reply_text("🚫 শুধুমাত্র অ্যাডমিন নতুন ভিডিও লিংক তৈরি করতে পারেন।")
        return

    copied = await message.copy(chat_id=CHANNEL_ID)
    token = encode_msg_id(copied.id)
    me = await client.get_me()
    share_link = f"https://t.me/{me.username}?start={token}"

    await message.reply_text(
        f"✅ ভিডিও প্রাইভেট চ্যানেলে সংরক্ষিত হয়েছে!\n\n"
        f"🔗 শেয়ার করার লিংক:\n{share_link}\n\n"
        f"🎟️ টোকেন:\n{token}"
    )


@app.on_message(filters.private & filters.text & ~filters.command(["start"]))
async def token_submit_handler(client: Client, message: Message):
    token = message.text.strip()
    msg_id = decode_token(token)
    if not msg_id:
        await message.reply_text(
            "দয়া করে সঠিক টোকেন পাঠান অথবা ভিডিও লিঙ্কে ক্লিক করুন।"
        )
        return

    try:
        await client.copy_message(
            chat_id=message.chat.id,
            from_chat_id=CHANNEL_ID,
            message_id=msg_id,
        )
    except Exception:
        await message.reply_text(
            "⚠️ ভিডিওটি খুঁজে পাওয়া যায়নি বা চ্যানেলে সমস্যা রয়েছে।"
        )


if name == "main":
    app.run()
