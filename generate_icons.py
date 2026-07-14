"""
Generate PWA icons for Factures — Menuiserie Amlou.

Creates 180x180, 192x192, and 512x512 PNG icons with a dark-blue
background and a bold gold "F" letter.  Colours are extracted from
the existing style.css so nothing is hard-coded.
"""

import os
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

STATIC_DIR = Path(__file__).parent / "static"
ICONS_DIR = STATIC_DIR / "icons"
CSS_FILE = STATIC_DIR / "style.css"


def extract_colours_from_css() -> tuple[str, str]:
    """Parse style.css and return (theme_color, accent_color) as hex strings."""
    css = CSS_FILE.read_text()

    # theme_color: the primary colour used in the header / navbar gradient
    gradient_match = re.search(
        r"linear-gradient\(\d+deg,\s*(#[0-9A-Fa-f]{6})", css
    )
    theme_color = gradient_match.group(1) if gradient_match else "#4472C4"

    # accent_color: the gold used on the save-button hover
    gold_match = re.search(r"\.btn-save\s*\{[^}]*background:\s*(#[0-9A-Fa-f]{6})", css)
    accent_color = gold_match.group(1) if gold_match else "#C9A84C"

    return theme_color, accent_color


def hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    h = hex_str.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def generate_icon(size: int, bg_rgb: tuple, fg_rgb: str, output_path: Path):
    img = Image.new("RGB", (size, size), bg_rgb)
    draw = ImageDraw.Draw(img)

    letter = "F"
    font_size = int(size * 0.55)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except OSError:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), letter, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (size - text_w) / 2
    y = (size - text_h) / 2 - bbox[1]
    draw.text((x, y), letter, fill=fg_rgb, font=font)

    img.save(output_path, "PNG")
    print(f"  Created {output_path} ({size}x{size})")


def main():
    ICONS_DIR.mkdir(parents=True, exist_ok=True)
    theme_color, accent_color = extract_colours_from_css()
    bg_rgb = hex_to_rgb(theme_color)
    fg_rgb = hex_to_rgb(accent_color)

    print(f"Theme colour (background): {theme_color}")
    print(f"Accent colour (letter):    {accent_color}")

    for size in (180, 192, 512):
        generate_icon(size, bg_rgb, fg_rgb, ICONS_DIR / f"icon-{size}.png")

    print("Done.")


if __name__ == "__main__":
    main()
