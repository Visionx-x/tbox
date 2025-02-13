import requests
import aria2p
from datetime import datetime
from status import format_progress_bar
import asyncio
import os
import time
import logging
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Initialize Aria2 API
aria2 = aria2p.API(
    aria2p.Client(
        host="http://localhost",
        port=6800,
        secret=""
    )
)

# Set global options for Aria2
options = {
    "max-tries": "50",
    "retry-wait": "3",
    "continue": "true"
}
aria2.set_global_options(options)

async def download_video(url, reply_msg, user_mention, user_id):
    try:
        # Fetch video download links from the API
        response = requests.get(f"https://teraboxvideodownloader.nepcoderdevs.workers.dev/?url={url}")
        response.raise_for_status()
        data = response.json()

        # Check if the response contains valid data
        if "response" not in data or not data["response"]:
            logging.error("Invalid response from API: No response data found.")
            await reply_msg.reply_text("Failed to retrieve video information.")
            return None, None, None

        # Extract download links and video information
        resolutions = data["response"][0]["resolutions"]
        fast_download_link = resolutions.get("Fast Download")
        hd_download_link = resolutions.get("HD Video")
        thumbnail_url = data["response"][0]["thumbnail"]
        video_title = data["response"][0]["title"]

        # Validate download links
        if not fast_download_link or not hd_download_link:
            logging.error("Download links are missing or invalid.")
            buttons = [
                [InlineKeyboardButton("🚀 HD Video", url=hd_download_link)],
                [InlineKeyboardButton("⚡ Fast Download", url=fast_download_link)]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await reply_msg.reply_text(
                "Fast Download Link For this Video is Broken, Download manually using the Link Below.",
                reply_markup=reply_markup
            )
            return None, None, None

        # Start downloading the video
        download = aria2.add_uris([fast_download_link])
        start_time = datetime.now()

        while not download.is_complete:
            download.update()
            percentage = download.progress
            done = download.completed_length
            total_size = download.total_length
            speed = download.download_speed
            eta = download.eta
            elapsed_time_seconds = (datetime.now() - start_time).total_seconds()

            # Update progress message
            progress_text = format_progress_bar(
                filename=video_title,
                percentage=percentage,
                done=done,
                total_size=total_size,
                status="Downloading",
                eta=eta,
                speed=speed,
                elapsed=elapsed_time_seconds,
                user_mention=user_mention,
                user_id=user_id,
                aria2p_gid=download.gid
            )
            await reply_msg.edit_text(progress_text)
            await asyncio.sleep(2)

        # Download complete, handle file and thumbnail
        if download.is_complete:
            file_path = download.files[0].path
            thumbnail_path = "thumbnail.jpg"

            # Download thumbnail
            thumbnail_response = requests.get(thumbnail_url)
            thumbnail_response.raise_for_status()  # Ensure thumbnail download is successful
            with open(thumbnail_path, "wb") as thumb_file:
                thumb_file.write(thumbnail_response.content)

            await reply_msg.edit_text("ᴜᴘʟᴏᴀᴅɪɴɢ...")
            return file_path, thumbnail_path, video_title

    except requests.RequestException as req_err:
        logging.error(f"Request error: {req_err}")
        await reply_msg.reply_text("Error fetching video data. Please try again later.")
    except Exception as e:
        logging.error(f"Error handling message: {e}")
        await reply_msg.reply_text("An unexpected error occurred. Please try again later.")

    return None, None, None

async def upload_video(client, file_path, thumbnail_path, video_title, reply_msg, collection_channel_id, user_mention, user_id, message):
    try:
        file_size = os.path.getsize(file_path)
        uploaded = 0
        start_time = datetime.now()
        last_update_time = time.time()

        async def progress(current, total):
            nonlocal uploaded, last_update_time
            uploaded = current
            percentage = (current / total) * 100
            elapsed_time_seconds = (datetime.now() - start_time).total_seconds()

            if time.time() - last_update_time > 2:
                progress_text = format_progress_bar(
                    filename=video_title,
                    percentage=
