import os, re, aiohttp, aiofiles
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
from youtubesearchpython.__future__ import VideosSearch

def truncate(text, limit=30):
    words = text.split()
    text1, text2 = "", ""
    for w in words:
        if len(text1 + " " + w) < limit:
            text1 += " " + w
        elif len(text2 + " " + w) < limit:
            text2 += " " + w
    return text1.strip(), text2.strip()

def crop_circle(img: Image.Image, output_size=400, border=20) -> Image.Image:
    img = img.resize((output_size - 2 * border, output_size - 2 * border))
    final = Image.new("RGBA", (output_size, output_size), "white")

    mask = Image.new("L", (output_size - 2 * border, output_size - 2 * border), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, output_size - 2 * border, output_size - 2 * border), fill=255)
    final.paste(img, (border, border), mask)

    outer_mask = Image.new("L", (output_size, output_size), 0)
    draw_outer = ImageDraw.Draw(outer_mask)
    draw_outer.ellipse((0, 0, output_size, output_size), fill=255)

    return Image.composite(final, Image.new("RGBA", final.size, (0, 0, 0, 0)), outer_mask)

async def get_bawaal_thumb(videoid: str):
    if os.path.exists(f"cache/{videoid}_bawaal.png"):
        return f"cache/{videoid}_bawaal.png"

    results = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
    result = (await results.next())["result"][0]

    title = re.sub(r"\W+", " ", result.get("title", "No Title")).strip().title()
    duration = result.get("duration", "0:00")
    thumbnail = result["thumbnails"][0]["url"].split("?")[0]
    channel = result.get("channel", {}).get("name", "Unknown Channel")
    views = result.get("viewCount", {}).get("short", "0 Views")

    async with aiohttp.ClientSession() as session:
        async with session.get(thumbnail) as resp:
            if resp.status == 200:
                async with aiofiles.open(f"cache/thumb_{videoid}.png", "wb") as f:
                    await f.write(await resp.read())

    album_art = Image.open(f"cache/thumb_{videoid}.png").convert("RGBA")
    album_art = album_art.resize((1280, 720)).filter(ImageFilter.BoxBlur(20))
    background = ImageEnhance.Brightness(album_art).enhance(0.6)

    # Purple gradient overlay
    gradient = Image.new("RGBA", background.size, "#5B2C6F")
    for y in range(background.size[1]):
        alpha = int(255 * (y / background.size[1]))
        ImageDraw.Draw(gradient).line([(0, y), (background.size[0], y)], fill=(91, 44, 111, alpha))
    bg = Image.alpha_composite(background, gradient)

    # Fonts
    font1 = ImageFont.truetype("SHUKLAMUSIC/assets/assets/font3.ttf", 50)
    font2 = ImageFont.truetype("SHUKLAMUSIC/assets/assets/font2.ttf", 28)
    font3 = ImageFont.truetype("SHUKLAMUSIC/assets/assets/font2.ttf", 26)

    circle_thumb = crop_circle(Image.open(f"cache/thumb_{videoid}.png"))
    bg.paste(circle_thumb, (100, 160), circle_thumb)

    draw = ImageDraw.Draw(bg)
    text_x = 550
    t1, t2 = truncate(title)

    draw.text((text_x, 180), t1, font=font1, fill="white")
    draw.text((text_x, 240), t2, font=font1, fill="white")
    draw.text((text_x, 310), f"{channel}  |  {views}", font=font2, fill="white")

    draw.text((text_x, 360), "00:24", font=font3, fill="white")
    draw.text((1150, 360), duration, font=font3, fill="white")

    bar_start = (text_x, 350)
    bar_mid = (text_x + 360, 350)
    bar_end = (text_x + 580, 350)
    draw.line([bar_start, bar_mid], fill="red", width=8)
    draw.line([bar_mid, bar_end], fill="white", width=8)
    draw.ellipse([(bar_mid[0] - 10, bar_mid[1] - 10), (bar_mid[0] + 10, bar_mid[1] + 10)], fill="white")

    # Controls image
    controls = Image.open("SHUKLAMUSIC/assets/assets/controls.png").convert("RGBA").resize((580, 62))
    bg.paste(controls, (text_x, 400), controls)

    output_path = f"cache/{videoid}_bawaal.png"
    bg.save(output_path)
    os.remove(f"cache/thumb_{videoid}.png")
    return output_path
