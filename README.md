# Telegram YouTube Downloader Bot

An asynchronous Telegram bot that lets users download YouTube videos or audio directly inside Telegram using `python-telegram-bot` v20+ and `yt-dlp`.

## Features

- 🎥 **Video Downloads**: Download YouTube videos in MP4 format.
- 🎵 **Audio Downloads**: Extract and download audio tracks in MP3/M4A format.
- ⚡ **Interactive Buttons**: Automatic metadata fetch (title, duration, channel) with inline keyboard selection.
- 🧹 **Automatic Cleanup**: Temporary files are deleted immediately after uploading to keep storage clean.
- ⚠️ **File Size Safety**: Respects Telegram's 50 MB bot API file upload limit.

## Project Structure

```
telegram-youtube-downloader/
├── src/
│   ├── bot.py          # Telegram bot handlers & application runner
│   ├── downloader.py   # YouTubeDownloader class (yt-dlp integration)
│   ├── utils.py        # Helpers for URL validation, file formatting & cleanup
│   └── config.py       # Configuration settings & environment variables
├── Bot.py              # Root entry point delegate
├── requirements.txt    # Required Python packages
└── README.md           # Documentation
```

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd telegram-youtube-downloader
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Bot Token:**
   - Either set your environment variable:
     ```bash
     export BOT_TOKEN="your_telegram_bot_token"
     ```
   - Or edit `src/config.py` with your bot token.

## Running the Bot

Run either:
```bash
python src/bot.py
```
or
```bash
python Bot.py
```

## Usage

1. Start a conversation with your bot on Telegram.
2. Send `/start` to see the welcome screen.
3. Send any YouTube URL (video or Shorts).
4. Click **🎥 Download Video** or **🎵 Download Audio**.
5. The bot will download and send the file directly to your Telegram chat!