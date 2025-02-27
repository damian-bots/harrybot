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
    """Generate a stylish and visually appealing YouTube thumbnail."""
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

        # Create a stylish gradient overlay
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 180))  # Semi-transparent black layer
        gradient = Image.new("L", (1, 720), color=0)
        for y in range(720):
            gradient.putpixel((0, y), int((y / 720) * 255))  # Stronger gradient effect
        gradient = gradient.resize(image.size)
        overlay.putalpha(gradient)

        # Blend image with overlay
        blended = Image.blend(image, overlay, alpha=0.6)

        # Draw elements on the image
        draw = ImageDraw.Draw(blended)
        font_title = ImageFont.truetype("AnonXMusic/assets/font.ttf", 50)
        font_info = ImageFont.truetype("AnonXMusic/assets/font2.ttf", 35)
        font_small = ImageFont.truetype("AnonXMusic/assets/font2.ttf", 28)

        # Add YouTube Play Button Overlay
        play_button = Image.open("AnonXMusic/assets/play_button.png").convert("RGBA")
        play_button = play_button.resize((180, 180))
        blended.paste(play_button, (550, 260), play_button)

        # Add Channel Name and Views with a glow effect
        draw.text((60, 550), f"{channel}  •  {views}", fill="white", font=font_info, stroke_width=2, stroke_fill="black")

        # Add Video Title with glow effect
        draw.text((60, 610), clear(title), fill="white", font=font_title, stroke_width=2, stroke_fill="black")

        # Enhanced progress bar with a red accent
        progress_bar_x_start, progress_bar_x_end = 60, 1220
        progress_bar_y = 680
        draw.line([(progress_bar_x_start, progress_bar_y), (progress_bar_x_end, progress_bar_y)],
                  fill="red", width=10)

        # Add a circular progress indicator
        draw.ellipse([(1180, 660), (1205, 685)], fill="white")

        # Add timestamps
        draw.text((55, 695), "00:00", fill="white", font=font_small, stroke_width=1, stroke_fill="black")
        draw.text((1175, 695), duration, fill="white", font=font_small, stroke_width=1, stroke_fill="black")

        # Save final thumbnail
        os.remove(temp_path)  # Remove temp image
        final_path = f"cache/{videoid}.png"
        blended.save(final_path)
        return final_path

    except Exception as e:
        print(e)
        return YOUTUBE_IMG_URL
