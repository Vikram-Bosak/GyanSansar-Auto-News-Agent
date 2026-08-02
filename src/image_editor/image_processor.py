import os
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance, ImageFilter
import logging
import re
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def ensure_font_downloaded(font_url, font_path):
    if not os.path.exists(font_path):
        try:
            r = requests.get(font_url)
            with open(font_path, 'wb') as f:
                f.write(r.content)
        except Exception as e:
            logging.error(f"Failed to download font: {e}")

def get_font(name="hindi", size=40):
    os.makedirs("assets/fonts", exist_ok=True)
    if name == "hindi":
        font_path = "assets/fonts/Mukta-Bold.ttf"
        font_url = "https://github.com/google/fonts/raw/main/ofl/mukta/Mukta-Bold.ttf"
    else:
        font_path = "assets/fonts/Mukta-Bold.ttf"
        font_url = "https://github.com/google/fonts/raw/main/ofl/mukta/Mukta-Bold.ttf"
        
    if os.path.exists(font_path) and os.path.getsize(font_path) < 10000:
        os.remove(font_path)
        
    ensure_font_downloaded(font_url, font_path)
    try:
        return ImageFont.truetype(font_path, size)
    except Exception as e:
        return ImageFont.load_default()

def center_crop(img, target_w, target_h):
    img_w, img_h = img.size
    ratio = max(target_w / img_w, target_h / img_h)
    new_w = int(img_w * ratio)
    new_h = int(img_h * ratio)
    img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return img_resized.crop((left, top, left + target_w, top + target_h))

def fetch_image(url):
    try:
        if url.startswith("http"):
            headers = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()
            return Image.open(BytesIO(r.content)).convert('RGB')
        else:
            return Image.open(url).convert('RGB')
    except Exception as e:
        return None

def render_multicolor_text_centered(draw, text, y_pos, font, max_width, img_width, text_color="#FFFFFF", highlight_color="#FFCC00"):
    tokens = []
    in_highlight = False
    for word in text.split():
        if "*" in word and word.find("*") < len(word) / 2:
            in_highlight = True
        ends_with = "*" in word[len(word)//2:] and len(word) > 1
        clean_word = word.replace("*", "")
        tokens.append({"text": clean_word, "highlight": in_highlight})
        if ends_with:
            in_highlight = False

    lines = []
    current_line = []
    
    def get_word_width(word):
        try:
            bbox = draw.textbbox((0, 0), word, font=font)
            return bbox[2] - bbox[0]
        except:
            return 0
    
    try:
        space_w = draw.textbbox((0, 0), " ", font=font)[2] - draw.textbbox((0, 0), " ", font=font)[0]
    except:
        space_w = 10

    def get_line_width(line_tokens):
        if not line_tokens: return 0
        return sum(get_word_width(t["text"]) for t in line_tokens) + space_w * (len(line_tokens) - 1)

    for token in tokens:
        current_line.append(token)
        if get_line_width(current_line) > max_width:
            current_line.pop()
            lines.append(current_line)
            current_line = [token]
    if current_line:
        lines.append(current_line)
        
    try:
        ascent, descent = font.getmetrics()
        line_height = ascent + descent
    except:
        line_height = 50
        
    actual_line_height = line_height * 0.95
    total_height = len(lines) * actual_line_height
    
    # Calculate starting Y to vertically center the text block inside the bottom box
    # Assuming the bottom box is from y=730 to y=1000 (height 270)
    # y_pos passed is the top of the box.
    box_height = 1080 - y_pos - 80 # Leave 80px for logo at the bottom
    start_y = y_pos + (box_height - total_height) // 2
    
    for line_tokens in lines:
        line_width = get_line_width(line_tokens)
        x_pos = (img_width - line_width) // 2
        for token in line_tokens:
            clean_word = token["text"]
            color = highlight_color if token["highlight"] else text_color
            draw.text((int(x_pos), int(start_y)), clean_word, font=font, fill=color)
            x_pos += get_word_width(clean_word) + space_w
        start_y += actual_line_height
    return start_y

def draw_circular_inset(base_img, inset_img, pos_x, pos_y, size=300, border_color="#FFFFFF"):
    if not inset_img: return
    # Resize and crop to square
    inset_cr = center_crop(inset_img, size, size)
    
    mask = Image.new('L', (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    
    circ = Image.new('RGBA', (size, size), (0,0,0,0))
    circ.paste(inset_cr.convert("RGBA"), (0,0), mask)
    
    # Draw border on the circle
    ImageDraw.Draw(circ).ellipse((0, 0, size, size), outline=border_color, width=6)
    
    base_img.paste(circ, (pos_x, pos_y), circ)

def add_watermark(base_img, text="रोचक तथ्य"):
    draw = ImageDraw.Draw(base_img)
    font = get_font("hindi", size=30)
    try:
        w = draw.textlength(text, font=font)
    except:
        w = 150
    # Add a simple bulb emoji or icon via text if possible, else just text
    watermark_text = f"💡 {text}"
    x = (base_img.width - w) // 2 - 20
    y = base_img.height - 50
    draw.text((x, y), watermark_text, font=font, fill="#FFFFFF")

def create_facebook_post(image_url, image_url_2=None, headline="", source_name="", output_path="output.jpg", logo_path="", hook_text="", circle_image_url=None, style_id=1):
    base_width, base_height = 1080, 1080
    base_img = Image.new('RGB', (base_width, base_height), color="#000000") 
    
    img1 = fetch_image(image_url) if image_url else None
    if not img1:
        img1 = Image.new('RGB', (base_width, base_height), color="#333333")
        
    img2 = fetch_image(image_url_2) if image_url_2 else None
    
    if not circle_image_url and img2:
        circle_image_url = img2
    elif circle_image_url:
        circle_image_url = fetch_image(circle_image_url)

    combined_text = f"{hook_text} {headline}" if hook_text else headline
    font_size = 55 if len(combined_text) < 100 else 45
    text_font = get_font("hindi", size=font_size)
    
    draw = ImageDraw.Draw(base_img)
    style_id = max(1, min(15, int(style_id)))

    # Box for text is typically y=700 to y=1080
    text_box_y = 700
    
    if style_id == 1:
        # Standard Solid Black Block
        img1_cr = center_crop(img1, base_width, text_box_y)
        base_img.paste(img1_cr, (0,0))
    elif style_id == 2:
        # Standard Gradient Bottom
        img1_cr = center_crop(img1, base_width, base_height)
        base_img.paste(img1_cr, (0,0))
        over = Image.new('RGBA', (base_width, base_height), (0,0,0,0))
        d_over = ImageDraw.Draw(over)
        # Gradient
        for i in range(text_box_y-200, base_height):
            alpha = int(255 * min(1.0, (i - (text_box_y-200)) / 200.0))
            d_over.line([(0, i), (base_width, i)], fill=(0,0,0,alpha))
        base_img.paste(over, (0,0), over)
    elif style_id == 3:
        # Top Right Circular Inset
        img1_cr = center_crop(img1, base_width, text_box_y)
        base_img.paste(img1_cr, (0,0))
        draw_circular_inset(base_img, circle_image_url or img1, base_width - 320, 40, size=280)
    elif style_id == 4:
        # Top Left Circular Inset
        img1_cr = center_crop(img1, base_width, text_box_y)
        base_img.paste(img1_cr, (0,0))
        draw_circular_inset(base_img, circle_image_url or img1, 40, 40, size=280)
    elif style_id == 5:
        # Split Screen Vertical
        img1_cr = center_crop(img1, base_width//2, text_box_y)
        img2_to_use = circle_image_url if circle_image_url else img1
        img2_cr = center_crop(img2_to_use, base_width//2, text_box_y)
        base_img.paste(img1_cr, (0,0))
        base_img.paste(img2_cr, (base_width//2, 0))
    elif style_id == 6:
        # Floating Center Image
        img1_cr = center_crop(img1, 980, 650)
        base_img.paste(img1_cr, (50,50))
    elif style_id == 7:
        # Thin White Border
        img1_cr = center_crop(img1, base_width, text_box_y)
        base_img.paste(img1_cr, (0,0))
        draw.rectangle([(20,20), (base_width-20, text_box_y-20)], outline="#FFFFFF", width=4)
    elif style_id == 8:
        # Blurred Background with sharp center
        bg = center_crop(img1, base_width, text_box_y).filter(ImageFilter.GaussianBlur(15))
        base_img.paste(bg, (0,0))
        img1_cr = center_crop(img1, 600, 600)
        base_img.paste(img1_cr, (240, 50))
    elif style_id == 9:
        # Vignette + Gradient
        img1_cr = center_crop(img1, base_width, base_height)
        base_img.paste(img1_cr, (0,0))
        over = Image.new('RGBA', (base_width, base_height), (0,0,0,0))
        d_over = ImageDraw.Draw(over)
        d_over.rectangle([(0,0), (base_width, base_height)], fill=(0,0,0,100)) # Darken all
        d_over.rectangle([(0, text_box_y-100), (base_width, base_height)], fill=(0,0,0,255)) # Solid black bottom
        base_img.paste(over, (0,0), over)
    elif style_id == 10:
        # Dual Circular Insets
        img1_cr = center_crop(img1, base_width, text_box_y)
        base_img.paste(img1_cr, (0,0))
        draw_circular_inset(base_img, circle_image_url or img1, 200, 50, size=250)
        draw_circular_inset(base_img, img1, 550, 50, size=250)
    elif style_id == 11:
        # Top 100px Black, Middle Image, Bottom Black
        draw.rectangle([(0,0), (base_width, 100)], fill="#000000")
        img1_cr = center_crop(img1, base_width, 600)
        base_img.paste(img1_cr, (0, 100))
    elif style_id == 12:
        # Horizontal Split Top
        img1_cr = center_crop(img1, base_width, 350)
        img2_to_use = circle_image_url if circle_image_url else img1
        img2_cr = center_crop(img2_to_use, base_width, 350)
        base_img.paste(img1_cr, (0,0))
        base_img.paste(img2_cr, (0,350))
    elif style_id == 13:
        # Diagonal Split Box
        img1_cr = center_crop(img1, base_width, base_height)
        base_img.paste(img1_cr, (0,0))
        poly = Image.new('RGBA', (base_width, base_height), (0,0,0,0))
        ImageDraw.Draw(poly).polygon([(0, 600), (base_width, 700), (base_width, base_height), (0, base_height)], fill=(0,0,0,255))
        base_img.paste(poly, (0,0), poly)
        text_box_y = 700
    elif style_id == 14:
        # Yellow Divider Line
        img1_cr = center_crop(img1, base_width, text_box_y)
        base_img.paste(img1_cr, (0,0))
        draw.rectangle([(0, text_box_y-10), (base_width, text_box_y)], fill="#FFCC00")
    elif style_id == 15:
        # Boxed Text (Yellow outline box on black bottom)
        img1_cr = center_crop(img1, base_width, text_box_y)
        base_img.paste(img1_cr, (0,0))
        draw.rectangle([(20, text_box_y+20), (base_width-20, base_height-60)], outline="#FFCC00", width=3)
    else:
        img1_cr = center_crop(img1, base_width, text_box_y)
        base_img.paste(img1_cr, (0,0))

    # Render Text in the bottom section
    render_multicolor_text_centered(draw, combined_text, text_box_y, text_font, base_width - 80, base_width, text_color="#FFFFFF", highlight_color="#FFCC00")
    
    # Add Logo/Watermark at the very bottom
    add_watermark(base_img, "रोचक तथ्य")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    base_img.save(output_path, quality=95)
    logging.info(f"Image saved to {output_path} with style {style_id}.")
    return output_path
