import os
import re

YOUTUBE_URL_REGEX = re.compile(
    r'^(https?://)?(www\.|m\.|music\.)?'
    r'(youtube\.com/(watch\?.*v=|embed/|v/|shorts/)|youtu\.be/)'
    r'([a-zA-Z0-9_-]{11})'
)

def is_valid_url(url: str) -> bool:
    """Check if the provided text is a valid YouTube URL."""
    if not url:
        return False
    return bool(YOUTUBE_URL_REGEX.search(url.strip()))

def format_bytes(size: float) -> str:
    """Format bytes to human readable string (KB, MB, GB)."""
    if not size:
        return "Unknown size"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

def format_duration(seconds: int) -> str:
    """Format duration in seconds to MM:SS or HH:MM:SS."""
    if not seconds or seconds <= 0:
        return "Unknown duration"
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

def cleanup_file(filepath: str) -> None:
    """Safely delete a file if it exists."""
    if filepath and os.path.exists(filepath):
        try:
            os.remove(filepath)
        except Exception:
            pass