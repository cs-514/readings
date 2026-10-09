from PIL import Image, ImageDraw
import os
out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public", "icons"); os.makedirs(out, exist_ok=True)
def make(size, name, pad=0.0):
    im = Image.new("RGB", (size, size), "#2b1b3d")
    d = ImageDraw.Draw(im)
    # soft inner glow
    for i in range(40):
        r = size * (0.5 - i * 0.008)
        c = (43 + i // 2, 27 + i // 3, 61 + i // 2)
        d.ellipse([size/2 - r, size/2 - r, size/2 + r, size/2 + r], fill=c)
    s = size * (1 - 2 * pad)
    cx, cy = size / 2, size / 2
    w = s * 0.11; h = s * 0.62; arm = s * 0.40
    gold = "#f1d38a"
    d.rounded_rectangle([cx - w/2, cy - h/2, cx + w/2, cy + h/2], radius=w*0.2, fill=gold)
    d.rounded_rectangle([cx - arm/2, cy - h*0.27, cx + arm/2, cy - h*0.27 + w], radius=w*0.2, fill=gold)
    im.save(os.path.join(out, name))
make(180, "apple-touch-icon.png"); make(192, "icon-192.png"); make(512, "icon-512.png"); make(512, "icon-maskable-512.png", pad=0.12); make(32, "favicon-32.png")
