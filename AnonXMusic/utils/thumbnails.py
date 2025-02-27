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
        if len(title) + len(word) < 50:
            title += " " + word
    return title.strip()


async def get_thumb(videoid):
    """Generate a unique and stylish pillow-style YouTube thumbnail."""
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

        # Apply soft pillow effect with rounded corners
        rounded_mask = Image.new("L", image.size, 0)
        draw_mask = ImageDraw.Draw(rounded_mask)
        draw_mask.rounded_rectangle([(10, 10), (1270, 710)], radius=50, fill=255)
        image.putalpha(rounded_mask)

        # Create a semi-transparent overlay with a soft gradient
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 150))  # Semi-transparent black
        gradient = Image.new("L", (1, 720), color=0)
        for y in range(720):
            gradient.putpixel((0, y), int((y / 720) * 200))
        gradient = gradient.resize(image.size)
        overlay.putalpha(gradient)

        # Add a soft glow effect
        glow = Image.new("RGBA", image.size, (255, 255, 255, 40))
        glow = glow.filter(ImageFilter.GaussianBlur(80))
        image = Image.alpha_composite(image, glow)

        # Blend original image with overlay
        blended = Image.alpha_composite(image, overlay)

        # Create a text background with blur effect
        text_bg = blended.copy().crop((40, 530, 1240, 720)).filter(ImageFilter.GaussianBlur(20))
        blended.paste(text_bg, (40, 530))

        # Draw elements on the image
        draw = ImageDraw.Draw(blended)
        font_title = ImageFont.truetype("AnonXMusic/assets/font.ttf", 50)
        font_info = ImageFont.truetype("AnonXMusic/assets/font2.ttf", 35)
        font_small = ImageFont.truetype("AnonXMusic/assets/font2.ttf", 28)

        # Add channel name and views with a stylish glow
        draw.text((60, 550), f"{channel}  •  {views}", fill="white", font=font_info, stroke_width=2, stroke_fill="black")

        # Add video title with a bold effect
        draw.text((60, 610), clear(title), fill="white", font=font_title, stroke_width=2, stroke_fill="black")

        # Enhanced progress bar with smooth curved edges
        progress_bar_x_start, progress_bar_x_end = 60, 1220
        progress_bar_y = 680
        draw.rounded_rectangle(
            [(progress_bar_x_start, progress_bar_y - 5), (progress_bar_x_end, progress_bar_y + 5)],
            radius=10,
            fill=(255, 0, 0),
            outline="white",
            width=3
        )

        # Add a circular progress indicator
        draw.ellipse([(1180, 660), (1205, 685)], fill="white", outline="black", width=2)

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
