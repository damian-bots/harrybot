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
    """Ensure the title is concise and visually balanced."""
    words = text.split(" ")
    title = ""
    for word in words:
        if len(title) + len(word) < 50:
            title += " " + word
    return title.strip()


async def get_thumb(videoid):
    """Generate a stylish YouTube thumbnail with a blurred background and a centered details box."""
    if os.path.isfile(f"cache/{videoid}.png"):
        return f"cache/{videoid}.png"

    url = f"https://www.youtube.com/watch?v={videoid}"
    try:
        results = VideosSearch(url, limit=1)
        for result in (await results.next())["result"]:
            try:
                title = result["title"]
                title = re.sub("\W+", " ", title)
                title = title.title()
            except:
                title = "Unsupported Title"
            try:
                duration = result["duration"]
            except:
                duration = "Unknown Mins"
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            try:
                views = result["viewCount"]["short"]
            except:
                views = "Unknown Views"
            try:
                channel = result["channel"]["name"]
            except:
                channel = "Unknown Channel"

        # Download the thumbnail
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status == 200:
                    temp_path = f"cache/temp_{videoid}.png"
                    async with aiofiles.open(temp_path, mode="wb") as f:
                        await f.write(await resp.read())

        # Open the image and apply a blurred background
        base_img = Image.open(temp_path)
        resized_img = resize_image(1280, 720, base_img).convert("RGBA")
        blurred_bg = resized_img.filter(ImageFilter.GaussianBlur(20))  # Strong blur effect
        dark_overlay = Image.new("RGBA", resized_img.size, (0, 0, 0, 120))
        blurred_bg = Image.alpha_composite(blurred_bg, dark_overlay)

        # Create a centered rectangle for song details
        details_box = Image.new("RGBA", (1000, 250), (0, 0, 0, 200))  # Semi-transparent dark box
        rounded_mask = Image.new("L", (1000, 250), 0)
        draw_mask = ImageDraw.Draw(rounded_mask)
        draw_mask.rounded_rectangle([(0, 0), (1000, 250)], radius=40, fill=255)  # Rounded corners
        details_box.putalpha(rounded_mask)

        # Paste the details box onto the blurred background
        blurred_bg.paste(details_box, (140, 230), details_box)

        # Draw text on the details box
        draw = ImageDraw.Draw(blurred_bg)
        font_title = ImageFont.truetype("AnonXMusic/assets/font.ttf", 50)
        font_info = ImageFont.truetype("AnonXMusic/assets/font2.ttf", 35)

        # Add YouTube details
        draw.text((180, 250), f"{channel}  •  {views}", fill="white", font=font_info, stroke_width=2, stroke_fill="black")
        draw.text((180, 310), clean_text(title), fill="white", font=font_title, stroke_width=2, stroke_fill="black")

        # **Progress Bar & Timestamps**
        progress_bar_x_start, progress_bar_x_end = 180, 1120
        progress_bar_y = 460
        draw.rounded_rectangle(
            [(progress_bar_x_start, progress_bar_y - 5), (progress_bar_x_end, progress_bar_y + 5)],
            radius=10,
            fill=(255, 0, 100),
            outline="white",
            width=2
        )

        # Circular progress indicator
        draw.ellipse([(1080, 440), (1105, 465)], fill="white", outline="black", width=2)

        # **Timestamps**
        draw.text((180, 470), "00:00", fill="white", font=font_info, stroke_width=1, stroke_fill="black")
        draw.text((1070, 470), duration, fill="white", font=font_info, stroke_width=1, stroke_fill="black")

        # Save final thumbnail
        os.remove(temp_path)  # Remove temp image
        final_path = f"cache/{videoid}.png"
        blurred_bg.save(final_path)
        return final_path

    except Exception as e:
        print(e)
        return YOUTUBE_IMG_URL
