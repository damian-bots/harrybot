import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from unidecode import unidecode
from youtubesearchpython.__future__ import VideosSearch

from AnonXMusic import app
from config import YOUTUBE_IMG_URL


def change_image_size(max_width, max_height, image):
    """Resize image while maintaining aspect ratio."""
    width_ratio = max_width / image.size[0]
    height_ratio = max_height / image.size[1]
    new_width = int(width_ratio * image.size[0])
    new_height = int(height_ratio * image.size[1])
    return image.resize((new_width, new_height))


def clear(text):
    """Ensure title does not exceed a certain length."""
    words = text.split(" ")
    title = ""
    for word in words:
        if len(title) + len(word) < 60:
            title += " " + word
    return title.strip()


async def get_thumb(videoid):
    """Generate an attractive YouTube thumbnail with enhanced design."""
    if os.path.isfile(f"cache/{videoid}.png"):
        return f"cache/{videoid}.png"

    url = f"https://www.youtube.com/watch?v={videoid}"
    try:
        results = VideosSearch(url, limit=1)
        for result in (await results.next())["result"]:
            title = re.sub(r"\W+", " ", result.get("title", "Unknown Title")).title()
            duration = result.get("duration", "Unknown Mins")
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            views = result.get("viewCount", {}).get("short", "Unknown Views")
            channel = result.get("channel", {}).get("name", "Unknown Channel")

        # Download the thumbnail image
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status == 200:
                    temp_path = f"cache/temp_{videoid}.png"
                    async with aiofiles.open(temp_path, mode="wb") as f:
                        await f.write(await resp.read())

        # Open and process image
        youtube = Image.open(temp_path)
        image = change_image_size(1280, 720, youtube).convert("RGBA")

        # Create a gradient overlay for aesthetics
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 180))  # Semi-transparent black layer
        gradient = Image.new("L", (1, 720), color=0)
        for y in range(720):
            gradient.putpixel((0, y), int((y / 720) * 200))  # Gradient effect
        gradient = gradient.resize(image.size)
        overlay.putalpha(gradient)

        # Blend image with overlay
        blended = Image.blend(image, overlay, alpha=0.5)

        # Draw elements on image
        draw = ImageDraw.Draw(blended)
        font_title = ImageFont.truetype("AnonXMusic/assets/font.ttf", 45)
        font_info = ImageFont.truetype("AnonXMusic/assets/font2.ttf", 30)
        font_small = ImageFont.truetype("AnonXMusic/assets/font2.ttf", 25)

        # Add channel name and views
        draw.text((50, 550), f"{channel}  •  {views}", fill="white", font=font_info)

        # Add video title
        draw.text((50, 600), clear(title), fill="white", font=font_title)

        # Add progress bar
        progress_bar_x_start, progress_bar_x_end = 50, 1230
        progress_bar_y = 670
        draw.line([(progress_bar_x_start, progress_bar_y), (progress_bar_x_end, progress_bar_y)],
                  fill="white", width=8)

        # Add circular progress indicator
        draw.ellipse([(1180, 655), (1205, 680)], fill="white")

        # Add time stamps
        draw.text((40, 690), "00:00", fill="white", font=font_small)
        draw.text((1185, 690), duration, fill="white", font=font_small)

        # Save final thumbnail
        os.remove(temp_path)  # Remove temp image
        final_path = f"cache/{videoid}.png"
        blended.save(final_path)
        return final_path

    except Exception as e:
        print(e)
        return YOUTUBE_IMG_URL
