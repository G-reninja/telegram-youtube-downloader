import os

# Telegram Bot Token (loaded securely from environment variable BOT_TOKEN)
BOT_TOKEN = os.getenv('BOT_TOKEN', '')


# Base directory for storing temporary downloads
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOWNLOAD_DIRECTORY = os.path.join(BASE_DIR, 'downloads')

# Path to existing ffmpeg executable
FFMPEG_PATH = os.getenv('FFMPEG_PATH', r'D:\VS Code\Python\vs code\udemy\youtube_downloader_app\ffmpeg.exe')

# Telegram Bot API limits file uploads to 50 MB
MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Ensure download directory exists
os.makedirs(DOWNLOAD_DIRECTORY, exist_ok=True)