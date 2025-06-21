import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
from youtubesearchpython.__future__ import VideosSearch

def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    return image.resize((newWidth, newHeight))

def truncate(text):
    parts = text.split(" ")
    text1 = ""
    text2 = ""
    for part in parts:
        if len(text1) + len(part) < 30:
            text1 += " " + part
        elif len(text2) + len(part) < 30:
            text2 += " " + part
    return [text1.strip(), text2.strip()]

def crop_center_circle(img, output_size, border, crop_scale=1.5):
    center_x = img.size[0] / 2
    center_y = img.size[1] / 2
    size = int(output_size * crop_scale)
    img = img.crop((
        center_x - size / 2,
        center_y - size / 2,
        center_x + size / 2,
        center_y + size / 2
    ))
    img = img.resize((output_size - 2 * border, output_size - 2 * border))
    final_img = Image.new("RGBA", (output_size, output_size), "white")

    mask_main = Image.new("L", (output_size - 2 * border, output_size - 2 * border), 0)
    draw_main = ImageDraw.Draw(mask_main)
    draw_main.ellipse((0, 0, output_size - 2 * border, output_size - 2 * border), fill=255)
    final_img.paste(img, (border, border), mask_main)

    mask_border = Image.new("L", (output_size, output_size), 0)
    draw_border = ImageDraw.Draw(mask_border)
    draw_border.ellipse((0, 0, output_size, output_size), fill=255)

    return Image.composite(final_img, Image.new("RGBA", final_img.size, (0, 0, 0, 0)), mask_border)

async def get_thumb(videoid):
    # Always generate a new thumbnail

    url = f"https://www.youtube.com/watch?v={videoid}"
    results = VideosSearch(url, limit=1)
    for result in (await results.next())["result"]:
        title = re.sub("\W+", " ", result.get("title", "Untitled")).title()
        duration = result.get("duration", "Unknown")
        thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        views = result.get("viewCount", {}).get("short", "Unknown Views")
        channel = result.get("channel", {}).get("name", "Unknown")

    # Download thumbnail
    async with aiohttp.ClientSession() as session:
        async with session.get(thumbnail) as resp:
            if resp.status == 200:
                async with aiofiles.open(f"cache/thumb{videoid}.png", mode="wb") as f:
                    await f.write(await resp.read())

    youtube = Image.open(f"cache/thumb{videoid}.png")
    resized_img = changeImageSize(1280, 720, youtube).convert("RGBA")

    # Purple blur background
    blurred_bg = resized_img.filter(ImageFilter.GaussianBlur(25))
    purple_overlay = Image.new("RGBA", blurred_bg.size, (140, 80, 180, 100))  # purple tint
    background = Image.alpha_composite(blurred_bg, purple_overlay)

    draw = ImageDraw.Draw(background)
    arial = ImageFont.truetype("SHUKLAMUSIC/assets/assets/font2.ttf", 30)
    font = ImageFont.truetype("SHUKLAMUSIC/assets/assets/font.ttf", 30)
    title_font = ImageFont.truetype("SHUKLAMUSIC/assets/assets/font3.ttf", 45)

    # Circular thumbnail
    circle_thumbnail = crop_center_circle(youtube, 400, 20)
    background.paste(circle_thumbnail, (120, 160), circle_thumbnail)

    # Title + Channel + Views
    text_x = 565
    lines = truncate(title)
    draw.text((text_x, 180), lines[0], fill="white", font=title_font)
    draw.text((text_x, 230), lines[1], fill="white", font=title_font)
    draw.text((text_x, 320), f"{channel}  |  {views[:23]}", fill="white", font=arial)

    # Progress bar
    total_bar_len = 580
    played_len = int(total_bar_len * 0.25)
    draw.line([(text_x, 380), (text_x + played_len, 380)], fill="white", width=9)
    draw.line([(text_x + played_len, text_x + total_bar_len), (text_x + total_bar_len, 380)], fill="#888", width=8)

    # Dot
    radius = 10
    dot_pos = text_x + played_len
    draw.ellipse([dot_pos - radius, 370 - radius, dot_pos + radius, 370 + radius], fill="white")

    # Time
    draw.text((text_x, 400), "00:24", fill="white", font=arial)
    draw.text((1080, 400), duration, fill="white", font=arial)

    # Controls image
    play_icons = Image.open("SHUKLAMUSIC/assets/assets/controls.png").resize((580, 62))
    background.paste(play_icons, (text_x, 450), play_icons)

    # Save final image
    save_path = f"cache/{videoid}_v4.png"
    try:
        os.remove(f"cache/thumb{videoid}.png")
    except:
        pass
    background.save(save_path)
    return save_path
