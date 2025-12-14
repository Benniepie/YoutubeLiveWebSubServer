import requests
from io import BytesIO
from PIL import Image
import math

VIDEO_ID = "63NoYLZXJfY"
URL = f"https://img.youtube.com/vi/{VIDEO_ID}/maxresdefault.jpg"

FLAIR_PALETTE = {
    "ORANGE_HITS":  (219, 143, 10),
    "GREEN_AID":    (14, 219, 10),
    "BLUE_MAP":     (0, 17, 255),
    "PINK_GEO":     (216, 10, 19),
    "RED_BREAKING": (255, 0, 0),
    "YELLOW_EXTRA": (255, 234, 0),
}

def get_closest_color(detected_rgb):
    min_distance = float('inf')
    closest_key = None
    for key, template_rgb in FLAIR_PALETTE.items():
        distance = math.sqrt(sum((detected_rgb[i] - template_rgb[i])**2 for i in range(3)))
        if distance < min_distance:
            min_distance = distance
            closest_key = key
    return closest_key, min_distance

def analyze_crop(img, name, box):
    crop = img.crop(box)
    avg_img = crop.resize((1, 1))
    rgb = avg_img.getpixel((0, 0))
    if isinstance(rgb, int): rgb = (rgb, rgb, rgb)
    rgb = rgb[:3]
    
    key, dist = get_closest_color(rgb)
    print(f"📍 {name} {box}:")
    print(f"   RGB: {rgb}")
    print(f"   Match: {key} (Dist: {dist:.2f})")
    print("-" * 20)

def main():
    print(f"📥 Downloading {URL}...")
    resp = requests.get(URL)
    img = Image.open(BytesIO(resp.content))
    w, h = img.size
    print(f"🖼️  Image Size: {w}x{h}")
    
    # 1. User's latest attempt (0, h-10, 10, h)
    analyze_crop(img, "User Attempt (Bottom-Left Edge)", (0, h-10, 10, h))
    
    # 2. Slightly Inset Bottom-Left
    analyze_crop(img, "Inset Bottom-Left (10, h-20, 20, h-10)", (10, h-20, 20, h-10))
    
    # 3. Higher Up (Above text?)
    analyze_crop(img, "Higher Left (20, h-100, 30, h-80)", (20, h-100, 30, h-80))
    
    # 4. Brand Stripes Area (estimated)
    # Assuming stripes are to the right of logo. 
    # Logo might be ~200px wide? 
    analyze_crop(img, "Stripes Candidate 1 (220, h-50, 230, h-40)", (220, h-50, 230, h-40))
    
    # Check top-left again just in case (User originally said x=40, y=40, maybe for different layout?)
    analyze_crop(img, "Top-Left (40, 40, 50, 50)", (40, 40, 50, 50))

if __name__ == "__main__":
    main()
