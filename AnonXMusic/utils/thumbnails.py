import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from unidecode import unidecode
from youtubesearchpython.__future__ import VideosSearch

from AnonXMusic import app
from config import YOUTUBE_IMG_URL


def resize_image(max_width, max_height, image):
    """Resize image while maintaining aspect ratio."""
    width_ratio = max_width / image.size[0]
    height_ratio = max_height / image.size[1]
    new_width = int(width_ratio * image.size[0])
    new_height = int(height_ratio * image.size[1])
    return image.resize((new_width, new_height))


def clean_text(text):
    """Ensure title is concise and visually balanced."""
    words = text.split(" ")
    title = ""
    for word in words:
        if len(title) + len(word) < 50:
            title += " " + word
    return title.strip()


async def get_thumb(videoid):
    """Generate a high-quality, stylish, and unique YouTube thumbnail."""
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

        # Download thumbnail
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status == 200:
                    temp_path = f"cache/temp_{videoid}.png"
                    async with aiofiles.open(temp_path, mode="wb") as f:
                        await f.write(await resp.read())

        # Open and resize image
        base_img = Image.open(temp_path)
        image = resize_image(1280, 720, base_img).convert("RGBA")

        # Create a depth effect with blur
        blurred_bg = image.filter(ImageFilter.GaussianBlur(20))
        dark_overlay = Image.new("RGBA", image.size, (0, 0, 0, 160))
        blended_bg = Image.alpha_composite(blurred_bg, dark_overlay)

        # Create rounded rectangle for a 3D effect
        rounded_thumb = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw_thumb = ImageDraw.Draw(rounded_thumb)
        draw_thumb.rounded_rectangle([(50, 50), (1230, 670)], radius=50, fill="white")
        blended_bg = Image.alpha_composite(blended_bg, rounded_thumb)

        # Add a soft spotlight effect
        glow_effect = Image.new("RGBA", image.size, (255, 255, 255, 30))
        glow_effect = glow_effect.filter(ImageFilter.GaussianBlur(120))
        blended_bg = Image.alpha_composite(blended_bg, glow_effect)

        # Create a cinematic black bar at the top & bottom
        draw = ImageDraw.Draw(blended_bg)
        draw.rectangle([(0, 0), (1280, 80)], fill=(0, 0, 0, 180))  # Top black bar
        draw.rectangle([(0, 640), (1280, 720)], fill=(0, 0, 0, 180))  # Bottom black bar

        # Load fonts
        font_title = ImageFont.truetype("AnonXMusic/assets/font.ttf", 55)
        font_info = ImageFont.truetype("AnonXMusic/assets/font2.ttf", 35)
        font_small = ImageFont.truetype("AnonXMusic/assets/font2.ttf", 30)

        # Add YouTube details
        draw.text((60, 20), f"{channel}  •  {views}", fill="white", font=font_info, stroke_width=2, stroke_fill="black")
        draw.text((60, 650), clean_text(title), fill="white", font=font_title, stroke_width=3, stroke_fill="black")

        # **Neon Glow Progress Bar**
        progress_bar_x_start, progress_bar_x_end = 60, 1220
        progress_bar_y = 690
        for i in range(5):  # Creates a glowing effect
            draw.rounded_rectangle(
                [(progress_bar_x_start, progress_bar_y - i), (progress_bar_x_end, progress_bar_y + i)],
                radius=10,
                fill=(255, 0, 100, 200 - i * 40),
            )

        # Circular progress dot with glow
        draw.ellipse([(1180, 670), (1205, 695)], fill="white", outline="black", width=2)

        # **Timestamps**
        draw.text((55, 700), "00:00", fill="white", font=font_small, stroke_width=1, stroke_fill="black")
        draw.text((1175, 700), duration, fill="white", font=font_small, stroke_width=1, stroke_fill="black")

        # Save final thumbnail
        os.remove(temp_path)  # Remove temp image
        final_path = f"cache/{videoid}.png"
        blended_bg.save(final_path)
        return final_path

    except Exception as e:
        print(e)
        return YOUTUBE_IMG_URL
