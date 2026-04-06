#!/usr/bin/env python3
"""
Social media image generator for Miniloop.
Composites text onto template backgrounds for Twitter/X posts.
"""

import argparse
import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import textwrap


# Configuration
IMAGE_WIDTH = 1200
IMAGE_HEIGHT = 675
MARGIN = 60
MAX_HEADLINE_WIDTH = IMAGE_WIDTH - (MARGIN * 2)

# Brand colors (placeholder - update with actual Miniloop colors)
COLORS = {
    "primary": "#6366F1",      # Indigo
    "secondary": "#8B5CF6",    # Purple
    "accent": "#EC4899",       # Pink
    "dark": "#1F2937",         # Dark gray
    "light": "#F9FAFB",        # Light gray
    "white": "#FFFFFF",
    "black": "#000000",
}

# Template-specific configurations
TEMPLATE_CONFIG = {
    "announcement": {
        "bg_colors": ["#6366F1", "#8B5CF6"],  # Gradient colors
        "text_color": "#FFFFFF",
        "headline_size": 72,
        "subheadline_size": 36,
        "align": "center",
    },
    "feature-launch": {
        "bg_colors": ["#1F2937", "#374151"],
        "text_color": "#FFFFFF",
        "headline_size": 64,
        "subheadline_size": 32,
        "align": "left",
    },
    "tip": {
        "bg_colors": ["#10B981", "#059669"],  # Green
        "text_color": "#FFFFFF",
        "headline_size": 56,
        "subheadline_size": 28,
        "align": "center",
    },
    "listicle": {
        "bg_colors": ["#3B82F6", "#1D4ED8"],  # Blue
        "text_color": "#FFFFFF",
        "headline_size": 60,
        "subheadline_size": 30,
        "align": "left",
    },
    "comparison": {
        "bg_colors": ["#F59E0B", "#D97706"],  # Amber
        "text_color": "#FFFFFF",
        "headline_size": 56,
        "subheadline_size": 28,
        "align": "center",
    },
}


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load font with fallback to default."""
    font_dir = Path(__file__).parent.parent / "fonts"

    # Try custom fonts first
    font_names = [
        "Inter-Bold.ttf" if bold else "Inter-Regular.ttf",
        "Inter-Bold.otf" if bold else "Inter-Regular.otf",
    ]

    for font_name in font_names:
        font_path = font_dir / font_name
        if font_path.exists():
            return ImageFont.truetype(str(font_path), size)

    # Fallback to system fonts
    system_fonts = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]

    for font_path in system_fonts:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue

    # Ultimate fallback
    return ImageFont.load_default()


def create_gradient(width: int, height: int, color1: str, color2: str) -> Image.Image:
    """Create a vertical gradient background."""
    img = Image.new("RGB", (width, height))

    # Convert hex to RGB
    c1 = tuple(int(color1.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
    c2 = tuple(int(color2.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))

    for y in range(height):
        ratio = y / height
        r = int(c1[0] * (1 - ratio) + c2[0] * ratio)
        g = int(c1[1] * (1 - ratio) + c2[1] * ratio)
        b = int(c1[2] * (1 - ratio) + c2[2] * ratio)

        for x in range(width):
            img.putpixel((x, y), (r, g, b))

    return img


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """Wrap text to fit within max_width."""
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = font.getbbox(test_line)
        width = bbox[2] - bbox[0]

        if width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]

    if current_line:
        lines.append(" ".join(current_line))

    return lines


def auto_scale_font(text: str, max_size: int, min_size: int, max_width: int, bold: bool = False) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    """Find the largest font size that fits the text within max_width."""
    for size in range(max_size, min_size - 1, -2):
        font = get_font(size, bold)
        lines = wrap_text(text, font, max_width)

        # Check if any line is too wide
        all_fit = True
        for line in lines:
            bbox = font.getbbox(line)
            if bbox[2] - bbox[0] > max_width:
                all_fit = False
                break

        if all_fit and len(lines) <= 4:  # Max 4 lines
            return font, lines

    # Return minimum size
    font = get_font(min_size, bold)
    return font, wrap_text(text, font, max_width)


def load_template_background(template_name: str) -> Image.Image:
    """Load template background or create gradient fallback."""
    template_dir = Path(__file__).parent.parent / "templates"
    template_path = template_dir / f"{template_name}.png"

    if template_path.exists():
        img = Image.open(template_path)
        return img.resize((IMAGE_WIDTH, IMAGE_HEIGHT), Image.Resampling.LANCZOS)

    # Create gradient fallback
    config = TEMPLATE_CONFIG.get(template_name, TEMPLATE_CONFIG["announcement"])
    return create_gradient(IMAGE_WIDTH, IMAGE_HEIGHT, config["bg_colors"][0], config["bg_colors"][1])


def add_logo(img: Image.Image) -> Image.Image:
    """Add logo watermark if available."""
    logo_path = Path(__file__).parent.parent / "assets" / "logo.png"

    if not logo_path.exists():
        return img

    logo = Image.open(logo_path).convert("RGBA")

    # Resize logo to reasonable size
    logo_height = 40
    aspect = logo.width / logo.height
    logo_width = int(logo_height * aspect)
    logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)

    # Position in bottom right
    x = IMAGE_WIDTH - logo_width - MARGIN
    y = IMAGE_HEIGHT - logo_height - 30

    # Paste with transparency
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    img.paste(logo, (x, y), logo)

    return img


def generate_image(
    template: str,
    headline: str,
    subheadline: str = "",
    filename: str = "output.png",
) -> str:
    """Generate social media image with text overlay."""

    config = TEMPLATE_CONFIG.get(template, TEMPLATE_CONFIG["announcement"])

    # Load or create background
    img = load_template_background(template)
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    draw = ImageDraw.Draw(img)

    # Auto-scale headline
    headline_font, headline_lines = auto_scale_font(
        headline,
        max_size=config["headline_size"],
        min_size=36,
        max_width=MAX_HEADLINE_WIDTH,
        bold=True
    )

    # Calculate text positioning
    line_height = headline_font.size + 10
    total_headline_height = len(headline_lines) * line_height

    # Calculate subheadline if present
    subheadline_lines = []
    subheadline_font = None
    total_subheadline_height = 0

    if subheadline:
        subheadline_font, subheadline_lines = auto_scale_font(
            subheadline,
            max_size=config["subheadline_size"],
            min_size=20,
            max_width=MAX_HEADLINE_WIDTH,
            bold=False
        )
        sub_line_height = subheadline_font.size + 8
        total_subheadline_height = len(subheadline_lines) * sub_line_height + 20  # +20 for gap

    # Total content height
    total_height = total_headline_height + total_subheadline_height

    # Start Y position (vertically centered)
    start_y = (IMAGE_HEIGHT - total_height) // 2

    # Draw headline
    text_color = config["text_color"]
    y = start_y

    for line in headline_lines:
        bbox = headline_font.getbbox(line)
        text_width = bbox[2] - bbox[0]

        if config["align"] == "center":
            x = (IMAGE_WIDTH - text_width) // 2
        else:  # left
            x = MARGIN

        # Draw shadow for better readability
        draw.text((x + 2, y + 2), line, font=headline_font, fill="#00000066")
        draw.text((x, y), line, font=headline_font, fill=text_color)

        y += line_height

    # Draw subheadline
    if subheadline and subheadline_font:
        y += 20  # Gap between headline and subheadline
        sub_line_height = subheadline_font.size + 8

        for line in subheadline_lines:
            bbox = subheadline_font.getbbox(line)
            text_width = bbox[2] - bbox[0]

            if config["align"] == "center":
                x = (IMAGE_WIDTH - text_width) // 2
            else:
                x = MARGIN

            draw.text((x + 1, y + 1), line, font=subheadline_font, fill="#00000044")
            draw.text((x, y), line, font=subheadline_font, fill=text_color)

            y += sub_line_height

    # Add logo
    img = add_logo(img)

    # Convert back to RGB for PNG saving
    if img.mode == "RGBA":
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3] if len(img.split()) > 3 else None)
        img = background

    # Save output
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / filename

    # Optimize for web
    img.save(output_path, "PNG", optimize=True)

    # Check file size
    file_size = output_path.stat().st_size
    print(f"Generated: {output_path}")
    print(f"File size: {file_size / 1024:.1f} KB")

    if file_size > 1_000_000:  # Over 1MB
        print("Warning: File size exceeds 1MB, consider reducing quality")

    return str(output_path)


def main():
    parser = argparse.ArgumentParser(description="Generate social media images")
    parser.add_argument("--template", required=True,
                        choices=["announcement", "feature-launch", "tip", "listicle", "comparison"],
                        help="Template name")
    parser.add_argument("--headline", required=True, help="Main headline text")
    parser.add_argument("--subheadline", default="", help="Subheadline or supporting text")
    parser.add_argument("--filename", required=True, help="Output filename")

    args = parser.parse_args()

    output_path = generate_image(
        template=args.template,
        headline=args.headline,
        subheadline=args.subheadline,
        filename=args.filename,
    )

    print(f"::set-output name=image_path::{output_path}")

    # Also set as environment file for newer GitHub Actions
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"image_path={output_path}\n")


if __name__ == "__main__":
    main()
