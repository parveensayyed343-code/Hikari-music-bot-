import asyncio
import yt_dlp
import re
from config import Config


YOUTUBE_REGEX = re.compile(
    r"(https?://)?(www\.)?"
    r"(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)"
    r"[\w\-]+"
)
SOUNDCLOUD_REGEX = re.compile(r"https?://(www\.)?soundcloud\.com/[\w\-/]+")


def _is_url(query: str) -> bool:
    return query.startswith("http://") or query.startswith("https://")


def _format_duration(seconds) -> str:
    if not seconds:
        return "Unknown"
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def _build_ydl_opts(cookies_file: str = "") -> dict:
    opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "extract_flat": False,
        "postprocessors": [],
        # Stream directly — no download
        "skip_download": True,
    }
    if cookies_file:
        opts["cookiefile"] = cookies_file
    return opts


class MusicHelper:
    def __init__(self):
        self.cookies_file = Config.COOKIES_FILE

    async def get_track_info(self, query: str) -> dict:
        """
        Accepts a YouTube/SoundCloud URL or a search query.
        Returns dict: {title, url, duration, source}
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._fetch_sync, query)

    def _fetch_sync(self, query: str) -> dict:
        ydl_opts = _build_ydl_opts(self.cookies_file)

        # If raw URL — extract directly
        if _is_url(query):
            search_query = query
        else:
            # Text search → YouTube
            search_query = f"ytsearch1:{query}"

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_query, download=False)

            # For search results, get the first entry
            if "entries" in info:
                info = info["entries"][0]

            # Get best audio URL
            audio_url = self._best_audio_url(info)

            # Determine source label
            if "soundcloud" in (info.get("webpage_url") or ""):
                source = "SoundCloud"
            else:
                source = "YouTube"

            return {
                "title": info.get("title", "Unknown Title"),
                "url": audio_url,
                "duration": _format_duration(info.get("duration")),
                "source": source,
                "webpage_url": info.get("webpage_url", ""),
            }

    def _best_audio_url(self, info: dict) -> str:
        """Pick the best audio-only stream URL."""
        formats = info.get("formats", [])

        # Prefer audio-only formats
        audio_formats = [
            f for f in formats
            if f.get("acodec") != "none" and f.get("vcodec") == "none"
        ]

        if audio_formats:
            # Sort by bitrate descending
            audio_formats.sort(key=lambda x: x.get("abr") or 0, reverse=True)
            return audio_formats[0]["url"]

        # Fallback: any format with audio
        for f in reversed(formats):
            if f.get("acodec") != "none" and f.get("url"):
                return f["url"]

        # Last resort: direct URL
        return info.get("url", "")
