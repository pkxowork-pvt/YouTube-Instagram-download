import os
import asyncio
import yt_dlp
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Apna Telegram Bot Token yahan replace karein
BOT_TOKEN = "8364646914:AAHbjZYCwZV0Jij34H-K4ty5AnO_sLm_WBw"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Namaste! Mujhe YouTube ya Instagram Reel ka link bhejiye, main video download karke bhej dunga."
    )

def download_video(url: str, output_path: str):
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': output_path,
        'max_filesize': 50 * 1024 * 1024,  # Telegram bot ki upload limit 50 MB hoti hai
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    # Valid platform check
    if not ("youtube.com" in url or "youtu.be" in url or "instagram.com" in url):
        await update.message.reply_text("❌ Kripya sirf YouTube ya Instagram ka link bhejein.")
        return

    status_msg = await update.message.reply_text("⏳ Video fetch ki ja rahi hai, thoda intezar karein...")
    file_name = f"video_{update.message.chat_id}.mp4"

    try:
        # Background worker thread taaki process block na ho
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, download_video, url, file_name)

        if os.path.exists(file_name):
            await status_msg.edit_text("📤 Video upload ho rahi hai...")
            with open(file_name, 'rb') as video_file:
                await update.message.reply_video(video=video_file, caption="✅ Yeh rahi aapki video!")
        else:
            await status_msg.edit_text("❌ Video download nahi ho saki ya file 50MB se badi hai.")

    except Exception as e:
        await status_msg.edit_text("⚠️ Error: Video process karne me dikkat aayi.")
        print(f"Error log: {e}")

    finally:
        # Local storage clean karna
        if os.path.exists(file_name):
            os.remove(file_name)
        try:
            await status_msg.delete()
        except:
            pass

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot chalu ho chuka hai...")
    app.run_polling()

if __name__ == '__main__':
    main()
    