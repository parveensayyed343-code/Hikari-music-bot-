import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── Required ──────────────────────────────────────────────────────────
    API_ID: int = int(os.environ.get("API_ID", 0))
    API_HASH: str = os.environ.get("API_HASH", "")
    BOT_TOKEN: str = os.environ.get("BOT_TOKEN", "")
    SESSION_STRING: str = os.environ.get("SESSION_STRING", "")

    # ── Optional ──────────────────────────────────────────────────────────
    # Max songs in queue per chat
    MAX_QUEUE_SIZE: int = int(os.environ.get("MAX_QUEUE_SIZE", 20))

    # yt-dlp cookies file path (optional, helps bypass age restrictions)
    COOKIES_FILE: str = os.environ.get("COOKIES_FILE", "")

    @classmethod
    def validate(cls):
        missing = []
        if not cls.API_ID:
            missing.append("API_ID")
        if not cls.API_HASH:
            missing.append("API_HASH")
        if not cls.BOT_TOKEN:
            missing.append("BOT_TOKEN")
        if not cls.SESSION_STRING:
            missing.append("SESSION_STRING")
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
