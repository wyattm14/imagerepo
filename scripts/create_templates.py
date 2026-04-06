#!/usr/bin/env python3
"""
Create placeholder template backgrounds.
Run this once to generate initial template images.
"""

from PIL import Image, ImageDraw
from pathlib import Path


IMAGE_WIDTH = 1200
IMAGE_HEIGHT = 675


TEMPLATES = {
    "announcement": {
        "colors": ["#6366F1", "#8B5CF6"],  # Indigo to purple
        "style": "diagonal",
    },
    "feature-launch": {
        "colors": ["#1F2937", "#374151"],  # Dark grays
        "style": "vertical",
    },
    "tip": {
        "colors": ["#10B981", "#059669"],  # Greens
        "style": "radial",
    },
    "listicle": {
        "colors": ["#3B82F6", "#1D4ED8"],  # Blues
        "style": "vertical",
    },
    "comparison": {
        "colors": ["#F59E0B", "#D97706"],  # Ambers
        "style": "split",
    },
}


def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def create_gradient_vertical(width: int, height: int, color1: str, color2: str) -> Image.Image:
    """Create a vertical gradient."""
    img = Image.new("RGB", (width, height))
    c1 = hex_to_rgb(color1)
    c2 = hex_to_rgb(color2)

    for y in range(height):
        ratio = y / height
        r = int(c1[0] * (1 - ratio) + c2[0] * ratio)
        g = int(c1[1] * (1 - ratio) + c2[1] * ratio)
        b = int(c1[2] * (1 - ratio) + c2[2] * ratio)

        for x in range(width):
            img.putpixel((x, y), (r, g, b))

    return img


def create_gradient_diagonal(width: int, height: int, color1: str, color2: str) -> Image.Image:
    """Create a diagonal gradient."""
    img = Image.new("RGB", (width, height))
    c1 = hex_to_rgb(color1)
    c2 = hex_to_rgb(color2)

    max_dist = width + height

    for y in range(height):
        for x in range(width):
            ratio = (x + y) / max_dist
            r = int(c1[0] * (1 - ratio) + c2[0] * ratio)
            g = int(c1[1] * (1 - ratio) + c2[1] * ratio)
            b = int(c1[2] * (1 - ratio) + c2[2] * ratio)
            img.putpixel((x, y), (r, g, b))

    return img


def create_gradient_radial(width: int, height: int, color1: str, color2: str) -> Image.Image:
    """Create a radial gradient from center."""
    img = Image.new("RGB", (width, height))
    c1 = hex_to_rgb(color1)
    c2 = hex_to_rgb(color2)

    cx, cy = width // 2, height // 2
    max_dist = ((width/2)**2 + (height/2)**2) ** 0.5

    for y in range(height):
        for x in range(width):
            dist = ((x - cx)**2 + (y - cy)**2) ** 0.5
            ratio = min(dist / max_dist, 1.0)
            r = int(c1[0] * (1 - ratio) + c2[0] * ratio)
            g = int(c1[1] * (1 - ratio) + c2[1] * ratio)
            b = int(c1[2] * (1 - ratio) + c2[2] * ratio)
            img.putpixel((x, y), (r, g, b))

    return img


def create_split(width: int, height: int, color1: str, color2: str) -> Image.Image:
    """Create a split/comparison background."""
    img = Image.new("RGB", (width, height))
    c1 = hex_to_rgb(color1)
    c2 = hex_to_rgb(color2)

    mid = width // 2

    # Left side gradient
    for y in range(height):
        for x in range(mid):
            ratio = y / height * 0.3  # Subtle gradient
            r = int(c1[0] * (1 - ratio) + c1[0] * 0.7 * ratio)
            g = int(c1[1] * (1 - ratio) + c1[1] * 0.7 * ratio)
            b = int(c1[2] * (1 - ratio) + c1[2] * 0.7 * ratio)
            img.putpixel((x, y), (r, g, b))

    # Right side gradient
    for y in range(height):
        for x in range(mid, width):
            ratio = y / height * 0.3
            r = int(c2[0] * (1 - ratio) + c2[0] * 0.7 * ratio)
            g = int(c2[1] * (1 - ratio) + c2[1] * 0.7 * ratio)
            b = int(c2[2] * (1 - ratio) + c2[2] * 0.7 * ratio)
            img.putpixel((x, y), (r, g, b))

    # Add center divider
    draw = ImageDraw.Draw(img)
    draw.line([(mid, 0), (mid, height)], fill="#FFFFFF", width=4)

    return img


def create_template(name: str, config: dict) -> Image.Image:
    """Create a template background based on config."""
    colors = config["colors"]
    style = config["style"]

    if style == "diagonal":
        return create_gradient_diagonal(IMAGE_WIDTH, IMAGE_HEIGHT, colors[0], colors[1])
    elif style == "radial":
        return create_gradient_radial(IMAGE_WIDTH, IMAGE_HEIGHT, colors[0], colors[1])
    elif style == "split":
        return create_split(IMAGE_WIDTH, IMAGE_HEIGHT, colors[0], colors[1])
    else:  # vertical
        return create_gradient_vertical(IMAGE_WIDTH, IMAGE_HEIGHT, colors[0], colors[1])


def main():
    template_dir = Path(__file__).parent.parent / "templates"
    template_dir.mkdir(exist_ok=True)

    for name, config in TEMPLATES.items():
        print(f"Creating template: {name}")
        img = create_template(name, config)
        output_path = template_dir / f"{name}.png"
        img.save(output_path, "PNG", optimize=True)
        print(f"  Saved: {output_path}")

    print("\nAll templates created!")


if __name__ == "__main__":
    main()
