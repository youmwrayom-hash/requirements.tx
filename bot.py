import os
import asyncio
import tempfile
from pathlib import Path

import yt_dlp
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.environ["BOT_TOKEN"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أرسل رابط فيديو Facebook وسأحاول تحميله لك."
    )


async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = (update.message.text or "").strip()

    if "facebook.com" not in url and "fb.watch" not in url:
        await update.message.reply_text("❌ أرسل رابط Facebook صحيح.")
        return

    status = await update.message.reply_text("⏳ جاري تحميل الفيديو...")

    with tempfile.TemporaryDirectory() as temp_dir:
        output = str(Path(temp_dir) / "video.%(ext)s")

        options = {
            "outtmpl": output,
            "format": "best[ext=mp4]/best",
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
        }

        try:
            def download():
                with yt_dlp.YoutubeDL(options) as ydl:
                    ydl.download([url])

            await asyncio.to_thread(download)

            files = list(Path(temp_dir).glob("video.*"))

            if not files:
                raise Exception("Video not found")

            video = files[0]

            if video.stat().st_size > 49 * 1024 * 1024:
                await status.edit_text(
                    "❌ الفيديو أكبر من الحد المسموح بإرساله عبر البوت."
                )
                return

            await status.edit_text("📤 جاري إرسال الفيديو...")

            with open(video, "rb") as f:
                await update.message.reply_video(
                    video=f,
                    supports_streaming=True
                )

            await status.delete()

        except Exception as e:
            print("ERROR:", e)
            await status.edit_text(
                "❌ تعذر تحميل الفيديو.\n"
                "قد يكون خاصًا أو محميًا أو غير مدعوم."
            )


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, download_video)
    )

    app.run_polling()


if __name__ == "__main__":
    main()
