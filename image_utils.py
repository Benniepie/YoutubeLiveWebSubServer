import requests
from io import BytesIO
from PIL import Image, ImageFilter
import math
from typing import Optional, Tuple

# Flair Palette (RGB)
FLAIR_PALETTE = {
    "ORANGE_HITS":  (219, 143, 10),    # Hits-and-Losses
    "GREEN_AID":    (14, 219, 10),    # MilitaryAid
    "BLUE_MAP":     (0, 17, 255),   # FrontLineMap
    "PINK_GEO":     (216, 10, 19),   # GeopoliticalNews
    "RED_BREAKING": (255, 0, 0),    # BreakingNews
    "YELLOW_EXTRA": (255, 234, 0),    # UpdateExtra
}

def download_image(url: str) -> Optional[BytesIO]:
    """Download image from URL into memory."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return BytesIO(response.content)
    except Exception as e:
        print(f"Error downloading image: {e}")
        return None

def get_closest_color(detected_rgb: Tuple[int, int, int]) -> Optional[str]:
    """Find the closest matching flair key for the given RGB color."""
    min_distance = float('inf')
    closest_key = None

    for key, template_rgb in FLAIR_PALETTE.items():
        distance = math.sqrt(
            (detected_rgb[0] - template_rgb[0])**2 +
            (detected_rgb[1] - template_rgb[1])**2 +
            (detected_rgb[2] - template_rgb[2])**2
        )
        if distance < min_distance:
            min_distance = distance
            closest_key = key
            
    return closest_key

def detect_flair_from_image(image_bytes: BytesIO) -> Optional[str]:
    """
    Detects the flair key based on the color of the 'Brand Stripes'
    in the top-left corner (40,40).
    """
    try:
        image_bytes.seek(0)
        img = Image.open(image_bytes)
        
        # Crop 10x10 box at bottom-left
        # x=40, y=height-50 (to leave 40px margin from bottom)
        width, height = img.size
        sample_box = img.crop((0, height - 20, 10, height-10)) 
        
        # Average color
        avg_color_img = sample_box.resize((1, 1))
        detected_rgb = avg_color_img.getpixel((0, 0))
        
        # Handle RGBA
        if isinstance(detected_rgb, int): # Grayscale
             detected_rgb = (detected_rgb, detected_rgb, detected_rgb)
        elif len(detected_rgb) == 4:
             detected_rgb = detected_rgb[:3]

        flair_key = get_closest_color(detected_rgb)
        print(f"  🎨 Detected Color: {detected_rgb} -> Matched: {flair_key}")
        return flair_key

    except Exception as e:
        print(f"Error analyzing image for flair: {e}")
        return None

def create_instagram_thumbnail(image_bytes: BytesIO) -> Optional[BytesIO]:
    """
    Creates a 4:5 Blur-Fill thumbnail (1080x1350).
    """
    try:
        image_bytes.seek(0)
        img = Image.open(image_bytes)
        
        target_width = 1080
        target_height = 1350
        
        # 1. Create Background (Blurred)
        aspect_ratio = img.width / img.height
        new_height = target_height
        new_width = int(new_height * aspect_ratio)
        
        background = img.resize((new_width, new_height))
        # Center crop the background to fit target width
        left = (new_width - target_width) / 2
        background = background.crop((left, 0, left + target_width, target_height))
        background = background.filter(ImageFilter.GaussianBlur(30))
        
        # 2. Paste Original in Center
        # Resize original to fit within target width
        foreground_width = target_width
        foreground_height = int(target_width / aspect_ratio)
        foreground = img.resize((foreground_width, foreground_height))
        
        y_pos = (target_height - foreground_height) // 2
        background.paste(foreground, (0, y_pos))
        
        # Save to BytesIO
        output = BytesIO()
        background.save(output, format="JPEG", quality=95)
        output.seek(0)
        return output
    except Exception as e:
        print(f"Error creating Instagram thumbnail: {e}")
        return None
