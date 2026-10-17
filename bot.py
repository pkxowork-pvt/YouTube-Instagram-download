import os
import asyncio
import uuid
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# 1. Bot Token daalein
BOT_TOKEN = "8364646914:AAHbjZYCwZV0Jij34H-K4ty5AnO_sLm_WBw"

# 2. Force Join Settings (Channel ka username ya ID '@' ke sath)
# Agar nahi lagana to ise None chhod sakte hain: REQUIRED_CHANNEL = None
REQUIRED_CHANNEL = "YouTubeInstagramdownload2026" 

# Pending URLs track karne ke liye dictionary
user_requests = {}

async def is_subscribed(bot, user_id: int) -> bool:
    if not REQUIRED_CHANNEL:
        return True
    try:
        member = await bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        return member.status in ["creator", "administrator", "member"]
    except Exception as e:
        print(f"Subscription check error: {e}")
        return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if REQUIRED_CHANNEL and not await is_subscribed(context.bot, user_id):
        keyboard = [
            [InlineKeyboardButton("📢 Channel Join Karein", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@', '')}")],
            [InlineKeyboardButton("✅ Check Karein", callback_data="check_join")]
        ]
        await update.message.reply_text(
            f"⚠️ Bot use karne ke liye pehle hamara channel join karein: {REQUIRED_CHANNEL}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    await update.message.reply_text(
        "👋 Namaste! Mujhe YouTube ya Instagram Reel ka link bhejiye.\n\nAap Video (MP4) ya Audio (MP3) me se choose kar sakte hain!"
    )

def download_media(url: str, output_path: str, is_audio: bool = False):
    if is_audio:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'max_filesize': 50 * 1024 * 1024,
            'quiet': True,
            'no_warnings': True,
        }
    else:
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': output_path,
            'max_filesize': 50 * 1024 * 1024,
            'quiet': True,
            'no_warnings': True,
        }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if REQUIRED_CHANNEL and not await is_subscribed(context.bot, user_id):
        keyboard = [
            [InlineKeyboardButton("📢 Channel Join Karein", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@', '')}")],
            [InlineKeyboardButton("✅ Check Karein", callback_data="check_join")]
        ]
        await update.message.reply_text(
            f"⚠️ Pehle hamare channel ko join karein: {REQUIRED_CHANNEL}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    url = update.message.text.strip()
    if not ("youtube.com" in url or "youtu.be" in url or "instagram.com" in url):
        await update.message.reply_text("❌ Kripya sirf YouTube ya Instagram ka valid link bhejein.")
        return

    # Unique request key generate karein
    req_id = str(uuid.uuid4())[:8]
    user_requests[req_id] = url

    keyboard = [
        [
            InlineKeyboardButton("🎬 Video (MP4)", callback_data=f"vid_{req_id}"),
            InlineKeyboardButton("🎵 Audio (MP3)", callback_data=f"aud_{req_id}")
        ]
    ]
    await update.message.reply_text("Format chunein:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.effective_user.id

    if data == "check_join":
        if await is_subscribed(context.bot, user_id):
            await query.edit_message_text("✅ Verification safal! Ab koi bhi link bhejein.")
        else:
            await query.answer("❌ Aapne abhi tak channel join nahi kiya hai!", show_alert=True)
        return

    action, req_id = data.split("_", 1)
    url = user_requests.get(req_id)

    if not url:
        await query.edit_message_text("⚠️ Link expire ho gaya hai, kripya link dobara bhejein.")
        return

    is_audio = (action == "aud")
    ext = "mp3" if is_audio else "mp4"
    file_name = f"download_{user_id}_{req_id}.{ext}"

    status_text = "🎵 Audio process ho rahi hai..." if is_audio else "🎬 Video process ho rahi hai..."
    await query.edit_message_text(f"⏳ {status_text}")

    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, download_media, url, file_name, is_audio)

        if os.path.exists(file_name):
            await query.edit_message_text("📤 File upload ho rahi hai...")
            with open(file_name, 'rb') as f:
                if is_audio:
                    await context.bot.send_audio(chat_id=user_id, audio=f, caption="✅ Audio Download Complete!")
                else:
                    await context.bot.send_video(chat_id=user_id, video=f, caption="✅ Video Download Complete!")
            await query.delete_message()
        else:
            await query.edit_message_text("❌ Download fail ho gaya ya file 50MB se badi hai.")
    except Exception as e:
        print(f"Error: {e}")
        await query.edit_message_text("⚠️ File fetch karne me problem aayi.")
    finally:
        if os.path.exists(file_name):
            os.remove(file_name)
        user_requests.pop(req_id, None)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))

    print("Updated bot chalu ho chuka hai...")
    app.run_polling()

if __name__ == '__main__':
    main()
    