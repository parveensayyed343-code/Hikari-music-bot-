import os
import asyncio
import logging
from aiohttp import web
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped
from pytgcalls.exceptions import NoActiveGroupCall
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import ChatAdminRequired
from config import Config
from queue_manager import MusicQueue
from music_helper import MusicHelper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = Client(
    "music_bot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    session_string=Config.SESSION_STRING
)

call_py = PyTgCalls(app)
queue = MusicQueue()
helper = MusicHelper()

HELP_TEXT = """
🎵 **Music Voice Chat Bot**

I stream music directly into Telegram voice chats!

**Commands:**
/play `<song name or URL>` — Add and stream music
/skip — Skip the current song
/stop — Stop and clear queue
/queue — Show upcoming tracks
/nowplaying — What's playing now
/help — Show this help

💡 Supports **YouTube** (name or URL) and **SoundCloud** URLs
🔊 Start a voice chat in your group, then use /play!
"""


@app.on_message(filters.command(["start", "help"]))
async def help_command(_, message: Message):
    await message.reply_text(HELP_TEXT)


@app.on_message(filters.command("play") & filters.group)
async def play_command(_, message: Message):
    chat_id = message.chat.id
    if len(message.command) < 2:
        await message.reply_text("❌ Usage: `/play <song name or URL>`")
        return
    query = " ".join(message.command[1:])
    status_msg = await message.reply_text("🔍 Searching...")
    try:
        track_info = await helper.get_track_info(query)
    except Exception as e:
        logger.error(f"Track fetch error: {e}")
        await status_msg.edit_text(f"❌ Could not find track: `{query}`")
        return
    queue.add(chat_id, track_info)
    pos = queue.size(chat_id)
    if queue.is_playing(chat_id):
        await status_msg.edit_text(
            f"➕ **Added to queue** (position #{pos})\n"
            f"🎵 {track_info['title']}\n"
            f"⏱ Duration: {track_info['duration']}"
        )
        return
    await status_msg.edit_text(f"⏳ Loading **{track_info['title']}**...")
    await start_playing(chat_id, message, status_msg)


async def start_playing(chat_id: int, message: Message, status_msg=None):
    track = queue.current(chat_id)
    if not track:
        return
    try:
        audio_stream = AudioPiped(track["url"])
        if queue.is_playing(chat_id):
            await call_py.change_stream(chat_id, audio_stream)
        else:
            await call_py.join_group_call(chat_id, audio_stream)
        queue.set_playing(chat_id, True)
        text = (
            f"▶️ **Now Playing**\n\n"
            f"🎵 {track['title']}\n"
            f"⏱ Duration: {track['duration']}\n"
            f"🔗 Source: {track['source']}"
        )
        if status_msg:
            await status_msg.edit_text(text)
        else:
            await message.reply_text(text)
    except NoActiveGroupCall:
        msg = "❌ No active voice chat! Start a voice chat first, then use /play."
        if status_msg:
            await status_msg.edit_text(msg)
        else:
            await message.reply_text(msg)
        queue.clear(chat_id)
    except ChatAdminRequired:
        msg = "❌ I need **admin rights** to join voice chat."
        if status_msg:
            await status_msg.edit_text(msg)
        else:
            await message.reply_text(msg)
        queue.clear(chat_id)
    except Exception as e:
        logger.error(f"Playback error: {e}")
        msg = f"❌ Error starting playback: {e}"
        if status_msg:
            await status_msg.edit_text(msg)
        else:
            await message.reply_text(msg)


@app.on_message(filters.command("skip") & filters.group)
async def skip_command(_, message: Message):
    chat_id = message.chat.id
    if not queue.is_playing(chat_id):
        await message.reply_text("❌ Nothing is playing right now.")
        return
    skipped = queue.current(chat_id)
    queue.next(chat_id)
    next_track = queue.current(chat_id)
    if next_track:
        await message.reply_text(f"⏭ Skipped **{skipped['title']}**\nLoading next track...")
        await start_playing(chat_id, message)
    else:
        try:
            await call_py.leave_group_call(chat_id)
        except Exception:
            pass
        queue.set_playing(chat_id, False)
        await message.reply_text(f"⏭ Skipped **{skipped['title']}**\n✅ Queue is empty.")


@app.on_message(filters.command("stop") & filters.group)
async def stop_command(_, message: Message):
    chat_id = message.chat.id
    if not queue.is_playing(chat_id):
        await message.reply_text("❌ Nothing is playing right now.")
        return
    queue.clear(chat_id)
    try:
        await call_py.leave_group_call(chat_id)
    except Exception:
        pass
    await message.reply_text("⏹ Stopped playback and cleared the queue.")


@app.on_message(filters.command("queue") & filters.group)
async def queue_command(_, message: Message):
    chat_id = message.chat.id
    tracks = queue.get_queue(chat_id)
    if not tracks:
        await message.reply_text("📭 The queue is empty.")
        return
    lines = ["🎶 **Current Queue:**\n"]
    for i, t in enumerate(tracks):
        prefix = "▶️" if i == 0 else f"{i}."
        lines.append(f"{prefix} {t['title']} `[{t['duration']}]`")
    await message.reply_text("\n".join(lines))


@app.on_message(filters.command("nowplaying") & filters.group)
async def nowplaying_command(_, message: Message):
    chat_id = message.chat.id
    track = queue.current(chat_id)
    if not track or not queue.is_playing(chat_id):
        await message.reply_text("❌ Nothing is playing right now.")
        return
    await message.reply_text(
        f"🎵 **Now Playing**\n\n"
        f"**{track['title']}**\n"
        f"⏱ Duration: {track['duration']}\n"
        f"🔗 Source: {track['source']}"
    )


@call_py.on_stream_end()
async def stream_ended(_, update):
    chat_id = update.chat_id
    queue.next(chat_id)
    next_track = queue.current(chat_id)
    if next_track:
        try:
            audio_stream = AudioPiped(next_track["url"])
            await call_py.change_stream(chat_id, audio_stream)
            logger.info(f"Auto-playing next: {next_track['title']}")
        except Exception as e:
            logger.error(f"Auto-play error: {e}")
            queue.set_playing(chat_id, False)
    else:
        try:
            await call_py.leave_group_call(chat_id)
        except Exception:
            pass
        queue.set_playing(chat_id, False)


async def health(request):
    return web.Response(text="Bot is running!")


async def start_health_server():
    app_web = web.Application()
    app_web.router.add_get("/", health)
    runner = web.AppRunner(app_web)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Health server running on port {port}")


async def main():
    await start_health_server()
    await app.start()
    await call_py.start()
    logger.info("🎵 Music Bot is running...")
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
