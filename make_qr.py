"""Kod QR z logo Suszanie na środku.  Użycie: python make_qr.py https://adres-strony/"""
import sys
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw
from qrcode.constants import ERROR_CORRECT_H

ROOT = Path(__file__).parent
url = sys.argv[1]

qr = qrcode.QRCode(error_correction=ERROR_CORRECT_H, box_size=40, border=4)
qr.add_data(url)
qr.make(fit=True)
img = qr.make_image(fill_color="#1f4d2b", back_color="white").convert("RGB")

logo = Image.open(ROOT / "assets" / "logo.png").convert("RGBA")
size = img.size[0]
target_h = int(size * 0.24)
logo = logo.resize((int(logo.width * target_h / logo.height), target_h), Image.LANCZOS)

pad = int(size * 0.025)
box = (logo.width + 2 * pad, logo.height + 2 * pad)
x0, y0 = (size - box[0]) // 2, (size - box[1]) // 2
ImageDraw.Draw(img).rounded_rectangle((x0, y0, x0 + box[0], y0 + box[1]), radius=pad * 2, fill="white")
img.paste(logo, (x0 + pad, y0 + pad), logo)

out = ROOT / "qr-kronika.png"
img.save(out)
print(out, img.size)
