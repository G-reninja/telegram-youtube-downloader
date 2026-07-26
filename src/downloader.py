import os
import glob
from yt_dlp import YoutubeDL

try:
    from .utils import format_bytes, format_duration
except ImportError:
    from utils import format_bytes, format_duration


class YouTubeDownloader:
    def __init__(self, download_dir=None):
        try:
            from .config import DOWNLOAD_DIRECTORY
        except ImportError:
            from config import DOWNLOAD_DIRECTORY
        self.download_dir = download_dir or DOWNLOAD_DIRECTORY
        os.makedirs(self.download_dir, exist_ok=True)


    def get_info(self, url: str) -> dict:
        """Extract metadata for a given YouTube URL without downloading."""
        try:
            from .config import BASE_DIR
        except ImportError:
            from config import BASE_DIR

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'skip_download': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'extractor_args': {
                'youtube': {
                    'player_client': ['mweb', 'android', 'web'],
                }
            },
        }


        cookie_path = os.path.join(BASE_DIR, 'cookies.txt')
        if os.path.exists(cookie_path):
            ydl_opts['cookiefile'] = cookie_path

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Handle playlist entries if a playlist URL was provided
            if 'entries' in info and len(info['entries']) > 0:
                info = info['entries'][0]

            title = info.get('title', 'YouTube Video')
            duration = info.get('duration', 0)
            thumbnail = info.get('thumbnail', '')
            uploader = info.get('uploader', 'Unknown Channel')
            filesize = info.get('filesize') or info.get('filesize_approx') or 0

            # Extract available unique video heights
            raw_heights = set()
            for f in info.get('formats', []):
                h = f.get('height')
                vcodec = f.get('vcodec', 'none')
                if h and vcodec != 'none' and h >= 144:
                    raw_heights.add(h)

            # Find best audio stream size
            audio_size = 0
            for f in info.get('formats', []):
                if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                    f_sz = f.get('filesize') or f.get('filesize_approx') or 0
                    if f_sz > audio_size:
                        audio_size = f_sz

            # Map height to best estimated video size
            height_map = {}
            for f in info.get('formats', []):
                h = f.get('height')
                vcodec = f.get('vcodec', 'none')
                if h and vcodec != 'none' and h >= 144:
                    f_sz = f.get('filesize') or f.get('filesize_approx') or 0
                    if h not in height_map or f_sz > height_map[h]:
                        height_map[h] = f_sz

            qualities_info = []
            for h in sorted(height_map.keys(), reverse=True):
                v_sz = height_map[h]
                est_sz = v_sz + audio_size if v_sz > 0 else 0

                if h >= 4320:
                    label_name = f"8K ({h}p)"
                elif h >= 2160:
                    label_name = f"4K ({h}p)"
                elif h >= 1440:
                    label_name = f"2K ({h}p)"
                elif h >= 720:
                    label_name = f"{h}p HD"
                else:
                    label_name = f"{h}p"

                qualities_info.append({
                    'height': h,
                    'label': label_name,
                    'filesize': est_sz,
                    'formatted_size': format_bytes(est_sz) if est_sz > 0 else "Unknown",
                })


            formatted_audio_size = format_bytes(audio_size) if audio_size > 0 else "Unknown"

            return {
                'id': info.get('id', ''),
                'title': title,
                'duration': duration,
                'formatted_duration': format_duration(duration),
                'thumbnail': thumbnail,
                'uploader': uploader,
                'filesize': filesize,
                'formatted_filesize': format_bytes(filesize) if filesize else "Unknown",
                'qualities': qualities_info,
                'audio_size': audio_size,
                'formatted_audio_size': formatted_audio_size,
            }


    def download_video(self, url: str, quality: str = 'best') -> dict:
        """Download video file in requested quality (e.g. '2160', '1440', '1080', '720', '480', etc.)."""
        try:
            from .config import FFMPEG_PATH, BASE_DIR, MAX_FILE_SIZE_BYTES
        except ImportError:
            from config import FFMPEG_PATH, BASE_DIR, MAX_FILE_SIZE_BYTES

        out_template = os.path.join(self.download_dir, '%(id)s_%(title).50s.%(ext)s')
        
        # Build format string based on requested quality
        if quality.isdigit():
            height = int(quality)
            format_str = f'bestvideo[height<={height}]+bestaudio/best[height<={height}]/best'
        else:
            format_str = 'bestvideo+bestaudio/best'

        ydl_opts = {
            'format': format_str,
            'outtmpl': out_template,
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'restrictfilenames': True,
            'merge_output_format': 'mp4',
            'socket_timeout': 30,
            'retries': 10,
            'fragment_retries': 10,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'extractor_args': {
                'youtube': {
                    'player_client': ['mweb', 'android', 'web'],
                }
            },
        }

        cookie_path = os.path.join(BASE_DIR, 'cookies.txt')
        if os.path.exists(cookie_path):
            ydl_opts['cookiefile'] = cookie_path

        # Check for custom ffmpeg location
        ffmpeg_loc = FFMPEG_PATH
        if not ffmpeg_loc:
            local_ffmpeg = os.path.join(BASE_DIR, 'ffmpeg.exe')
            if os.path.exists(local_ffmpeg):
                ffmpeg_loc = local_ffmpeg

        if ffmpeg_loc and os.path.exists(ffmpeg_loc):
            ydl_opts['ffmpeg_location'] = ffmpeg_loc

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if 'entries' in info and len(info['entries']) > 0:
                info = info['entries'][0]

            expected_path = ydl.prepare_filename(info)
            filepath = self._find_downloaded_file(info.get('id', ''), expected_path)

            if not filepath or not os.path.exists(filepath):
                raise FileNotFoundError("Downloaded video file could not be found.")

            file_size = os.path.getsize(filepath)

            return {
                'filepath': filepath,
                'title': info.get('title', 'Video'),
                'duration': info.get('duration', 0),
                'filesize': file_size,
                'formatted_filesize': format_bytes(file_size),
                'quality': quality,
            }




    def download_audio(self, url: str) -> dict:
        """Download audio file (M4A/MP3 preferred)."""
        try:
            from .config import FFMPEG_PATH, BASE_DIR
        except ImportError:
            from config import FFMPEG_PATH, BASE_DIR

        out_template = os.path.join(self.download_dir, '%(id)s_%(title).50s.%(ext)s')
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'outtmpl': out_template,
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'restrictfilenames': True,
            'socket_timeout': 30,
            'retries': 10,
            'fragment_retries': 10,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'extractor_args': {
                'youtube': {
                    'player_client': ['mweb', 'android', 'web'],
                }
            },
        }


        cookie_path = os.path.join(BASE_DIR, 'cookies.txt')
        if os.path.exists(cookie_path):
            ydl_opts['cookiefile'] = cookie_path

        ffmpeg_loc = FFMPEG_PATH
        if not ffmpeg_loc:
            local_ffmpeg = os.path.join(BASE_DIR, 'ffmpeg.exe')
            if os.path.exists(local_ffmpeg):
                ffmpeg_loc = local_ffmpeg

        if ffmpeg_loc and os.path.exists(ffmpeg_loc):
            ydl_opts['ffmpeg_location'] = ffmpeg_loc

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if 'entries' in info and len(info['entries']) > 0:
                info = info['entries'][0]

            expected_path = ydl.prepare_filename(info)
            filepath = self._find_downloaded_file(info.get('id', ''), expected_path)

            if not filepath or not os.path.exists(filepath):
                raise FileNotFoundError("Downloaded audio file could not be found.")

            file_size = os.path.getsize(filepath)
            return {
                'filepath': filepath,
                'title': info.get('title', 'Audio'),
                'duration': info.get('duration', 0),
                'filesize': file_size,
                'formatted_filesize': format_bytes(file_size),
            }


    def _find_downloaded_file(self, video_id: str, expected_path: str) -> str:
        """Locate the actual downloaded file on disk."""
        if os.path.exists(expected_path):
            return expected_path
        
        # Look for matching file ID in download directory
        pattern = os.path.join(self.download_dir, f"*{video_id}*")
        matches = glob.glob(pattern)
        if matches:
            return matches[0]
        return None
