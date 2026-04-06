#!/usr/bin/env python3
"""
Component-based social media image generator.
Pass JSON config to generate images with text overlays on backgrounds.
"""

import argparse
import json
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from typing import Optional


# Get repo root
REPO_ROOT = Path(__file__).parent.parent
BACKGROUNDS_DIR = REPO_ROOT / "backgrounds"
OUTPUT_DIR = REPO_ROOT / "output"
FONTS_DIR = REPO_ROOT / "fonts"


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load font with fallbacks."""
    font_names = [
        "Inter-Bold.ttf" if bold else "Inter-Regular.ttf",
        "Inter-Bold.otf" if bold else "Inter-Regular.otf",
    ]

    for font_name in font_names:
        font_path = FONTS_DIR / font_name
        if font_path.exists():
            return ImageFont.truetype(str(font_path), size)

    # System font fallbacks
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

    return ImageFont.load_default()


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

    return lines if lines else [""]


def auto_fit_text(text: str, max_width: int, max_size: int, min_size: int, bold: bool = False) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    """Find optimal font size and wrap text."""
    for size in range(max_size, min_size - 1, -2):
        font = get_font(size, bold)
        lines = wrap_text(text, font, max_width)

        all_fit = all(
            font.getbbox(line)[2] - font.getbbox(line)[0] <= max_width
            for line in lines
        )

        if all_fit and len(lines) <= 4:
            return font, lines

    font = get_font(min_size, bold)
    return font, wrap_text(text, font, max_width)


class ImageGenerator:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.img: Optional[Image.Image] = None
        self.draw: Optional[ImageDraw.ImageDraw] = None
        self.margin = 60
        self.content_width = width - (self.margin * 2)

    def load_background(self, bg_name: str):
        """Load and resize background image."""
        # Try with and without extension
        bg_path = BACKGROUNDS_DIR / bg_name
        if not bg_path.exists():
            bg_path = BACKGROUNDS_DIR / f"{bg_name}.png"
        if not bg_path.exists():
            bg_path = BACKGROUNDS_DIR / f"{bg_name}.jpg"

        if not bg_path.exists():
            raise FileNotFoundError(f"Background not found: {bg_name}")

        self.img = Image.open(bg_path).convert("RGBA")
        self.img = self.img.resize((self.width, self.height), Image.Resampling.LANCZOS)
        self.draw = ImageDraw.Draw(self.img)

    def add_overlay(self, style: str = "dark", opacity: float = 0.5):
        """Add semi-transparent overlay for text readability."""
        overlay = Image.new("RGBA", (self.width, self.height))
        overlay_draw = ImageDraw.Draw(overlay)

        if style == "dark":
            color = (0, 0, 0, int(255 * opacity))
        elif style == "light":
            color = (255, 255, 255, int(255 * opacity))
        elif style == "gradient_bottom":
            # Gradient from transparent to dark at bottom
            for y in range(self.height):
                ratio = max(0, (y - self.height * 0.4)) / (self.height * 0.6)
                alpha = int(255 * opacity * ratio)
                overlay_draw.line([(0, y), (self.width, y)], fill=(0, 0, 0, alpha))
        elif style == "gradient_top":
            for y in range(self.height):
                ratio = 1 - (y / (self.height * 0.6))
                ratio = max(0, ratio)
                alpha = int(255 * opacity * ratio)
                overlay_draw.line([(0, y), (self.width, y)], fill=(0, 0, 0, alpha))
        elif style == "vignette":
            # Dark edges, lighter center
            cx, cy = self.width // 2, self.height // 2
            max_dist = ((self.width/2)**2 + (self.height/2)**2) ** 0.5
            for y in range(self.height):
                for x in range(self.width):
                    dist = ((x - cx)**2 + (y - cy)**2) ** 0.5
                    ratio = (dist / max_dist) ** 1.5
                    alpha = int(255 * opacity * ratio)
                    overlay.putpixel((x, y), (0, 0, 0, alpha))
        else:
            color = (0, 0, 0, int(255 * opacity))

        if style in ["dark", "light"]:
            overlay_draw.rectangle([(0, 0), (self.width, self.height)], fill=color)

        self.img = Image.alpha_composite(self.img, overlay)
        self.draw = ImageDraw.Draw(self.img)

    def add_card(self, x: int, y: int, width: int, height: int,
                 color: str = "#FFFFFF", opacity: float = 0.95, radius: int = 20):
        """Add a rounded card/container."""
        card = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        card_draw = ImageDraw.Draw(card)

        # Parse color
        if color.startswith("#"):
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
        else:
            r, g, b = 255, 255, 255

        fill = (r, g, b, int(255 * opacity))
        card_draw.rounded_rectangle([(0, 0), (width-1, height-1)], radius=radius, fill=fill)

        self.img.paste(card, (x, y), card)
        self.draw = ImageDraw.Draw(self.img)

    def draw_text(self, text: str, x: int, y: int, font: ImageFont.FreeTypeFont,
                  color: str = "#FFFFFF", shadow: bool = True, align: str = "left") -> int:
        """Draw text with optional shadow. Returns Y position after text."""
        lines = wrap_text(text, font, self.content_width)
        line_height = font.size + 10

        for line in lines:
            bbox = font.getbbox(line)
            text_width = bbox[2] - bbox[0]

            if align == "center":
                draw_x = x + (self.content_width - text_width) // 2
            elif align == "right":
                draw_x = x + self.content_width - text_width
            else:
                draw_x = x

            if shadow:
                self.draw.text((draw_x + 2, y + 2), line, font=font, fill="#00000088")
            self.draw.text((draw_x, y), line, font=font, fill=color)
            y += line_height

        return y

    def render_headline(self, config: dict, y_offset: int) -> int:
        """Render headline component."""
        text = config.get("text", "")
        size = config.get("size", 72)
        color = config.get("color", "#FFFFFF")
        align = config.get("align", "center")

        font, lines = auto_fit_text(text, self.content_width, size, 36, bold=True)

        y = y_offset
        for line in lines:
            bbox = font.getbbox(line)
            text_width = bbox[2] - bbox[0]

            if align == "center":
                x = (self.width - text_width) // 2
            elif align == "right":
                x = self.width - self.margin - text_width
            else:
                x = self.margin

            # Shadow
            self.draw.text((x + 3, y + 3), line, font=font, fill="#00000099")
            self.draw.text((x, y), line, font=font, fill=color)
            y += font.size + 12

        return y + 20

    def render_subheadline(self, config: dict, y_offset: int) -> int:
        """Render subheadline component."""
        text = config.get("text", "")
        size = config.get("size", 36)
        color = config.get("color", "#FFFFFFCC")
        align = config.get("align", "center")

        font, lines = auto_fit_text(text, self.content_width, size, 24, bold=False)

        y = y_offset
        for line in lines:
            bbox = font.getbbox(line)
            text_width = bbox[2] - bbox[0]

            if align == "center":
                x = (self.width - text_width) // 2
            elif align == "right":
                x = self.width - self.margin - text_width
            else:
                x = self.margin

            self.draw.text((x + 2, y + 2), line, font=font, fill="#00000066")
            self.draw.text((x, y), line, font=font, fill=color)
            y += font.size + 8

        return y + 15

    def render_list(self, config: dict, y_offset: int) -> int:
        """Render numbered or bulleted list."""
        items = config.get("items", [])
        size = config.get("size", 32)
        color = config.get("color", "#FFFFFF")
        numbered = config.get("numbered", True)
        align = config.get("align", "left")

        font = get_font(size, bold=True)
        item_font = get_font(size, bold=False)

        y = y_offset

        for i, item in enumerate(items, 1):
            prefix = f"{i}." if numbered else "•"
            prefix_width = font.getbbox(prefix + " ")[2]

            if align == "center":
                # Calculate total width for centering
                item_bbox = item_font.getbbox(item)
                total_width = prefix_width + (item_bbox[2] - item_bbox[0])
                x = (self.width - total_width) // 2
            else:
                x = self.margin + 20

            # Draw number/bullet
            self.draw.text((x + 2, y + 2), prefix, font=font, fill="#00000066")
            self.draw.text((x, y), prefix, font=font, fill=config.get("accent_color", "#FFD700"))

            # Draw item text
            self.draw.text((x + prefix_width + 2, y + 2), item, font=item_font, fill="#00000066")
            self.draw.text((x + prefix_width, y), item, font=item_font, fill=color)

            y += size + 20

        return y + 10

    def render_quote(self, config: dict, y_offset: int) -> int:
        """Render a quote with attribution."""
        text = config.get("text", "")
        author = config.get("author", "")
        size = config.get("size", 42)
        color = config.get("color", "#FFFFFF")

        # Quote marks
        quote_font = get_font(80, bold=True)
        self.draw.text((self.margin, y_offset - 20), '"', font=quote_font, fill="#FFFFFF44")

        # Quote text
        font, lines = auto_fit_text(text, self.content_width - 40, size, 28, bold=False)

        y = y_offset + 30
        for line in lines:
            self.draw.text((self.margin + 22, y + 2), line, font=font, fill="#00000066")
            self.draw.text((self.margin + 20, y), line, font=font, fill=color)
            y += font.size + 10

        # Author
        if author:
            y += 15
            author_font = get_font(24, bold=True)
            self.draw.text((self.margin + 22, y + 1), f"— {author}", font=author_font, fill="#00000044")
            self.draw.text((self.margin + 20, y), f"— {author}", font=author_font, fill="#FFFFFFAA")
            y += 30

        return y + 20

    def render_stat(self, config: dict, y_offset: int) -> int:
        """Render a big statistic number with label."""
        value = config.get("value", "0")
        label = config.get("label", "")
        color = config.get("color", "#FFFFFF")
        accent = config.get("accent_color", "#FFD700")
        align = config.get("align", "center")

        # Big number
        value_font = get_font(120, bold=True)
        value_bbox = value_font.getbbox(str(value))
        value_width = value_bbox[2] - value_bbox[0]

        if align == "center":
            x = (self.width - value_width) // 2
        else:
            x = self.margin

        y = y_offset
        self.draw.text((x + 4, y + 4), str(value), font=value_font, fill="#00000088")
        self.draw.text((x, y), str(value), font=value_font, fill=accent)
        y += 130

        # Label
        if label:
            label_font = get_font(32, bold=False)
            label_bbox = label_font.getbbox(label)
            label_width = label_bbox[2] - label_bbox[0]

            if align == "center":
                x = (self.width - label_width) // 2

            self.draw.text((x + 2, y + 2), label, font=label_font, fill="#00000066")
            self.draw.text((x, y), label, font=label_font, fill=color)
            y += 50

        return y

    def render_badge(self, config: dict, y_offset: int) -> int:
        """Render a small badge/tag."""
        text = config.get("text", "")
        bg_color = config.get("bg_color", "#FFD700")
        text_color = config.get("text_color", "#000000")
        align = config.get("align", "center")

        font = get_font(20, bold=True)
        bbox = font.getbbox(text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        padding_x, padding_y = 20, 10
        badge_width = text_width + padding_x * 2
        badge_height = text_height + padding_y * 2

        if align == "center":
            x = (self.width - badge_width) // 2
        elif align == "right":
            x = self.width - self.margin - badge_width
        else:
            x = self.margin

        # Draw badge background
        self.add_card(x, y_offset, badge_width, badge_height, bg_color, 1.0, radius=badge_height//2)

        # Draw text
        self.draw.text((x + padding_x, y_offset + padding_y - 2), text, font=font, fill=text_color)

        return y_offset + badge_height + 20

    def render_cta(self, config: dict, y_offset: int) -> int:
        """Render call-to-action button."""
        text = config.get("text", "Learn More")
        bg_color = config.get("bg_color", "#FFFFFF")
        text_color = config.get("text_color", "#000000")
        align = config.get("align", "center")

        font = get_font(28, bold=True)
        bbox = font.getbbox(text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        padding_x, padding_y = 40, 16
        btn_width = text_width + padding_x * 2
        btn_height = text_height + padding_y * 2

        if align == "center":
            x = (self.width - btn_width) // 2
        elif align == "right":
            x = self.width - self.margin - btn_width
        else:
            x = self.margin

        self.add_card(x, y_offset, btn_width, btn_height, bg_color, 1.0, radius=btn_height//2)
        self.draw.text((x + padding_x, y_offset + padding_y - 2), text, font=font, fill=text_color)

        return y_offset + btn_height + 20

    def render_divider(self, config: dict, y_offset: int) -> int:
        """Render a horizontal divider line."""
        color = config.get("color", "#FFFFFF44")
        width = config.get("width", self.content_width // 2)

        x = (self.width - width) // 2
        self.draw.line([(x, y_offset), (x + width, y_offset)], fill=color, width=2)

        return y_offset + 30

    def render_spacer(self, config: dict, y_offset: int) -> int:
        """Add vertical space."""
        height = config.get("height", 40)
        return y_offset + height

    def generate(self, config: dict) -> str:
        """Generate image from config."""
        # Get dimensions from background or config
        bg_name = config.get("background", "background-1-horizontal")

        # Detect dimensions from filename
        if "square" in bg_name:
            self.width, self.height = 1080, 1080
        elif "verticle" in bg_name or "vertical" in bg_name:
            self.width, self.height = 1080, 1350
        else:
            self.width, self.height = 1200, 675

        # Override if specified
        self.width = config.get("width", self.width)
        self.height = config.get("height", self.height)
        self.content_width = self.width - (self.margin * 2)

        # Load background
        self.load_background(bg_name)

        # Add overlay if specified
        if "overlay" in config:
            overlay_config = config["overlay"]
            if isinstance(overlay_config, str):
                self.add_overlay(overlay_config)
            else:
                self.add_overlay(
                    overlay_config.get("style", "dark"),
                    overlay_config.get("opacity", 0.5)
                )

        # Calculate starting Y based on layout
        layout = config.get("layout", "center")
        components = config.get("components", [])

        # Estimate total height
        estimated_height = 0
        for comp in components:
            comp_type = comp.get("type", "")
            if comp_type == "headline":
                estimated_height += 100
            elif comp_type == "subheadline":
                estimated_height += 60
            elif comp_type == "list":
                estimated_height += len(comp.get("items", [])) * 55
            elif comp_type == "quote":
                estimated_height += 150
            elif comp_type == "stat":
                estimated_height += 180
            elif comp_type == "badge":
                estimated_height += 50
            elif comp_type == "cta":
                estimated_height += 70
            elif comp_type == "divider":
                estimated_height += 30
            elif comp_type == "spacer":
                estimated_height += comp.get("height", 40)

        if layout == "center":
            y = (self.height - estimated_height) // 2
        elif layout == "top":
            y = self.margin + 20
        elif layout == "bottom":
            y = self.height - estimated_height - self.margin
        else:
            y = self.margin

        # Render components
        component_renderers = {
            "headline": self.render_headline,
            "subheadline": self.render_subheadline,
            "list": self.render_list,
            "quote": self.render_quote,
            "stat": self.render_stat,
            "badge": self.render_badge,
            "cta": self.render_cta,
            "divider": self.render_divider,
            "spacer": self.render_spacer,
        }

        for comp in components:
            comp_type = comp.get("type", "")
            renderer = component_renderers.get(comp_type)
            if renderer:
                y = renderer(comp, y)

        # Save
        OUTPUT_DIR.mkdir(exist_ok=True)
        filename = config.get("filename", "output.png")
        output_path = OUTPUT_DIR / filename

        # Convert to RGB for saving
        rgb_img = Image.new("RGB", self.img.size, (255, 255, 255))
        rgb_img.paste(self.img, mask=self.img.split()[3] if self.img.mode == "RGBA" else None)
        rgb_img.save(output_path, "PNG", optimize=True)

        print(f"Generated: {output_path}")
        print(f"Size: {output_path.stat().st_size / 1024:.1f} KB")

        return str(output_path)


def main():
    parser = argparse.ArgumentParser(description="Generate social images from JSON config")
    parser.add_argument("--config", "-c", help="JSON config string or path to JSON file")
    parser.add_argument("--example", action="store_true", help="Print example configs")

    args = parser.parse_args()

    if args.example:
        examples = {
            "announcement": {
                "background": "background-horizontal-dark",
                "overlay": {"style": "dark", "opacity": 0.4},
                "filename": "example-announcement.png",
                "components": [
                    {"type": "badge", "text": "NEW", "bg_color": "#FFD700"},
                    {"type": "headline", "text": "AI Employees Are Here"},
                    {"type": "subheadline", "text": "Automate your GTM workflow with intelligent agents"},
                    {"type": "cta", "text": "Get Started"}
                ]
            },
            "listicle": {
                "background": "background-1-horizontal",
                "overlay": "dark",
                "filename": "example-listicle.png",
                "components": [
                    {"type": "headline", "text": "5 Ways to 10x Productivity", "size": 64},
                    {"type": "spacer", "height": 20},
                    {"type": "list", "items": ["Automate repetitive tasks", "Use AI assistants", "Batch similar work", "Set clear priorities", "Take strategic breaks"], "numbered": True}
                ]
            },
            "quote": {
                "background": "background-square-1",
                "overlay": {"style": "gradient_bottom", "opacity": 0.7},
                "filename": "example-quote.png",
                "components": [
                    {"type": "spacer", "height": 100},
                    {"type": "quote", "text": "The best way to predict the future is to create it.", "author": "Peter Drucker"}
                ]
            },
            "stat": {
                "background": "background-horizontal-dark",
                "overlay": {"style": "vignette", "opacity": 0.5},
                "filename": "example-stat.png",
                "components": [
                    {"type": "stat", "value": "10x", "label": "Faster than manual outreach", "accent_color": "#00FF88"},
                    {"type": "subheadline", "text": "Join 1,000+ teams using Miniloop"}
                ]
            }
        }
        print(json.dumps(examples, indent=2))
        return

    if not args.config:
        parser.print_help()
        return

    # Load config
    if args.config.startswith("{"):
        config = json.loads(args.config)
    else:
        with open(args.config) as f:
            config = json.load(f)

    generator = ImageGenerator(1200, 675)
    generator.generate(config)


if __name__ == "__main__":
    main()
