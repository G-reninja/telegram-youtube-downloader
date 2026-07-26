import asyncio
import logging
import os
import sys

# Ensure src directory is in python path
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.request import HTTPXRequest
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

try:
    from . import config
    from .downloader import YouTubeDownloader
    from .utils import is_valid_url, cleanup_file
except ImportError:
    import config
    from downloader import YouTubeDownloader
    from utils import is_valid_url, cleanup_file


# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize YouTube Downloader
downloader = YouTubeDownloader()



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message on /start command."""
    welcome_text = (
        "👋 **Welcome to Rohit's YouTube Downloader Bot!**\n\n"
        "Send me any valid YouTube video or Shorts link, and I will help you download "
        "the video or audio directly in Telegram.\n\n"
        "📌 **Features:**\n"
        "• 🎥 Dynamic Video Resolutions (8K, 4K, 1080p, 720p, 480p)\n"
        "• 🎵 High Quality Audio (MP3)\n"
        "• 📊 Real-time File Size Estimates\n"
        "• 🛡️ Smart Data Protection & Bandwidth Saver\n\n"
        "👑 *Developed by Rohit | Type /about for more info*"
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help message on /help command."""
    help_text = (
        "❓ **How to use this bot:**\n\n"
        "1. Copy a YouTube link (e.g., `https://www.youtube.com/watch?v=...` or `https://youtu.be/...`).\n"
        "2. Paste and send the link to this chat.\n"
        "3. Select your preferred **Resolution** or **Audio** from the interactive buttons.\n"
        "4. Wait a few moments while the bot processes and uploads your file!\n\n"
        "⚠️ *Note: Telegram Bot API limits uploads to 50 MB.*"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send developer info on /about command."""
    about_text = (
        "🤖 **YouTube Downloader Bot**\n\n"
        "👑 **Developer & Creator:** Rohit\n"
        "🚀 **Built With:** Python, python-telegram-bot, yt-dlp & FFmpeg\n\n"
        "✨ **Key Features:**\n"
        "• 🎥 Dynamic Quality Selection (8K, 4K, 1080p HD, 720p HD, 480p)\n"
        "• 🎵 Best Quality Audio Extraction\n"
        "• 📊 Real-time File Size Estimates\n"
        "• 🛡️ Zero Data-Wasted Pre-Download Check\n\n"
        "© Created with ❤️ by Rohit"
    )
    await update.message.reply_text(about_text, parse_mode='Markdown')



async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming user messages containing YouTube URLs."""
    url = update.message.text.strip() if update.message.text else ""

    if not is_valid_url(url):
        await update.message.reply_text(
            "❌ **Invalid YouTube URL!**\n\nPlease send a valid YouTube video or Shorts link.",
            parse_mode='Markdown'
        )
        return

    status_msg = await update.message.reply_text("🔍 *Fetching video details...*", parse_mode='Markdown')

    try:
        # Fetch metadata in non-blocking background thread
        info = await asyncio.to_thread(downloader.get_info, url)
        video_id = info.get('id', 'temp')

        # Save URL and video info mapping in user_data
        if 'urls' not in context.user_data:
            context.user_data['urls'] = {}
        if 'video_info' not in context.user_data:
            context.user_data['video_info'] = {}

        context.user_data['urls'][video_id] = url
        context.user_data['video_info'][video_id] = info

        caption = (
            f"🎬 **{info.get('title', 'YouTube Video')}**\n\n"
            f"👤 **Channel:** {info.get('uploader', 'Unknown')}\n"
            f"⏱ **Duration:** {info.get('formatted_duration', 'Unknown')}\n\n"
            f"⚠️ *Note: Telegram Bot API limits file uploads to 50 MB max. Qualities marked with ⚠️ [>50MB] exceed Telegram's limit and cannot be uploaded.*\n\n"
            f"👇 *Select resolution or format to download:*"
        )

        qualities_info = info.get('qualities', [])
        audio_size = info.get('audio_size', 0)
        audio_size_str = info.get('formatted_audio_size', 'Unknown')

        keyboard = []
        for q in qualities_info:
            h = q['height']
            lbl = q['label']
            sz = q['formatted_size']
            bytes_sz = q['filesize']

            if bytes_sz > config.MAX_FILE_SIZE_BYTES:
                button_text = f"⚠️ 🎥 {lbl} (~{sz}) [>50MB]"
            else:
                button_text = f"🎥 {lbl} (~{sz})"

            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"vid:{h}:{video_id}")])

        if audio_size > config.MAX_FILE_SIZE_BYTES:
            audio_text = f"⚠️ 🎵 Audio Only (~{audio_size_str}) [>50MB]"
        else:
            audio_text = f"🎵 Audio Only (MP3) (~{audio_size_str})"

        keyboard.append([InlineKeyboardButton(audio_text, callback_data=f"aud:best:{video_id}")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await status_msg.edit_text(caption, reply_markup=reply_markup, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error fetching video info: {e}")
        await status_msg.edit_text(f"❌ **Failed to fetch video details:** {str(e)}")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button clicks for video or audio download with pre-download size checks."""
    query = update.callback_query
    await query.answer()

    data = query.data
    parts = data.split(":")
    if len(parts) != 3:
        return

    mode, quality, video_id = parts
    urls_map = context.user_data.get('urls', {})
    url = urls_map.get(video_id)
    info = context.user_data.get('video_info', {}).get(video_id, {})

    if not url:
        await query.edit_message_text("⚠️ **Session expired.** Please send the YouTube link again.")
        return

    is_video = (mode == "vid")
    mode_str = f"{quality}p Video 🎥" if is_video else "Audio 🎵"

    # Pre-download file size check to save bandwidth
    est_bytes = 0
    est_formatted = "Unknown"

    if is_video and quality.isdigit():
        req_height = int(quality)
        for q in info.get('qualities', []):
            if q['height'] == req_height:
                est_bytes = q['filesize']
                est_formatted = q['formatted_size']
                break
    elif not is_video:
        est_bytes = info.get('audio_size', 0)
        est_formatted = info.get('formatted_audio_size', 'Unknown')

    if est_bytes > config.MAX_FILE_SIZE_BYTES:
        await query.edit_message_text(
            f"⚠️ **File Size Limit Exceeded!**\n\n"
            f"The **{mode_str}** is estimated at **~{est_formatted}**, which exceeds Telegram's 50 MB bot upload limit.\n\n"
            f"🛑 *Download stopped immediately to save your internet data (0 bytes downloaded).* \n\n"
            f"💡 *Please send the link again and select a resolution under 50 MB (e.g. 720p or 480p).*",
            parse_mode='Markdown'
        )
        return

    await query.edit_message_text(f"⏬ *Downloading {mode_str}... Please wait.*", parse_mode='Markdown')



    filepath = None
    try:
        if is_video:
            res = await asyncio.to_thread(downloader.download_video, url, quality)
        else:
            res = await asyncio.to_thread(downloader.download_audio, url)

        filepath = res.get('filepath')
        filesize = res.get('filesize', 0)
        title = res.get('title', 'Downloaded File')

        if filesize > config.MAX_FILE_SIZE_BYTES:
            await query.edit_message_text(
                f"⚠️ **File size limit exceeded!**\n\n"
                f"The downloaded {mode_str} is **{res.get('formatted_filesize')}**, which exceeds "
                f"Telegram's 50 MB limit for bot uploads.\n\n"
                f"💡 *Tip: Please send the link again and choose a lower resolution (e.g. 720p or 480p)!*",
                parse_mode='Markdown'
            )
            return

        await query.edit_message_text(f"⬆️ *Uploading {mode_str} to Telegram...*", parse_mode='Markdown')


        with open(filepath, 'rb') as file_obj:
            if is_video:
                await context.bot.send_video(
                    chat_id=query.message.chat_id,
                    video=file_obj,
                    caption=f"🎥 **{title}**",
                    supports_streaming=True,
                    parse_mode='Markdown',
                    read_timeout=300,
                    write_timeout=300,
                    connect_timeout=60,
                )
            else:
                await context.bot.send_audio(
                    chat_id=query.message.chat_id,
                    audio=file_obj,
                    title=title,
                    caption=f"🎵 **{title}**",
                    parse_mode='Markdown',
                    read_timeout=300,
                    write_timeout=300,
                    connect_timeout=60,
                )

        try:
            await query.edit_message_text(f"✅ **Downloaded successfully!**", parse_mode='Markdown')
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Download or upload error: {e}", exc_info=True)
        try:
            await query.edit_message_text(f"❌ **An error occurred during process:** {str(e)}")
        except Exception:
            pass


    finally:
        if filepath:
            cleanup_file(filepath)


def main() -> None:
    """Start the Telegram bot."""
    if not config.BOT_TOKEN or config.BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        logger.error("BOT_TOKEN is not configured! Please set BOT_TOKEN in src/config.py")
        return

    print("🚀 Starting Telegram YouTube Downloader Bot...")
    request = HTTPXRequest(
        connect_timeout=60.0,
        read_timeout=300.0,
        write_timeout=300.0
    )
    app = ApplicationBuilder().token(config.BOT_TOKEN).request(request).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("developer", about_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))


    print("✅ Bot is online and listening for messages!")
    app.run_polling()



if __name__ == '__main__':
    main()