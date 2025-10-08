#!/usr/bin/env python
"""
Generate PWA icons and favicon from the haleway_square.png image.
"""
from PIL import Image
import os

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_IMAGE = os.path.join(BASE_DIR, 'static', 'img', 'haleway_square.png')
OUTPUT_DIR = os.path.join(BASE_DIR, 'static', 'img', 'icons')

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# PWA icon sizes (standard sizes for web app manifests)
PWA_SIZES = [
    (72, 72),
    (96, 96),
    (128, 128),
    (144, 144),
    (152, 152),
    (192, 192),
    (384, 384),
    (512, 512),
]

# Favicon sizes
FAVICON_SIZES = [
    (16, 16),
    (32, 32),
    (48, 48),
    (64, 64),
]

def generate_icons():
    """Generate all icon sizes from the source image."""
    print(f"Loading source image: {SOURCE_IMAGE}")

    try:
        # Load the source image
        img = Image.open(SOURCE_IMAGE)

        # Convert to RGBA if not already
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        print(f"Source image size: {img.size}")

        # Generate PWA icons
        print("\nGenerating PWA icons...")
        for width, height in PWA_SIZES:
            output_path = os.path.join(OUTPUT_DIR, f'icon-{width}x{height}.png')
            resized = img.resize((width, height), Image.Resampling.LANCZOS)
            resized.save(output_path, 'PNG', optimize=True)
            print(f"  ✓ Generated {width}x{height} → {output_path}")

        # Generate favicons
        print("\nGenerating favicons...")
        for width, height in FAVICON_SIZES:
            output_path = os.path.join(OUTPUT_DIR, f'favicon-{width}x{height}.png')
            resized = img.resize((width, height), Image.Resampling.LANCZOS)
            resized.save(output_path, 'PNG', optimize=True)
            print(f"  ✓ Generated {width}x{height} → {output_path}")

        # Generate main favicon.ico (multi-size)
        print("\nGenerating favicon.ico...")
        favicon_path = os.path.join(BASE_DIR, 'static', 'favicon.ico')
        favicon_images = [img.resize(size, Image.Resampling.LANCZOS) for size in FAVICON_SIZES]
        favicon_images[0].save(
            favicon_path,
            format='ICO',
            sizes=[(img.width, img.height) for img in favicon_images]
        )
        print(f"  ✓ Generated favicon.ico → {favicon_path}")

        # Generate Apple Touch Icon
        print("\nGenerating Apple Touch Icon...")
        apple_touch_path = os.path.join(OUTPUT_DIR, 'apple-touch-icon.png')
        apple_touch = img.resize((180, 180), Image.Resampling.LANCZOS)
        apple_touch.save(apple_touch_path, 'PNG', optimize=True)
        print(f"  ✓ Generated 180x180 → {apple_touch_path}")

        print("\n✅ All icons generated successfully!")
        print(f"\nIcons saved to: {OUTPUT_DIR}")
        print(f"Favicon saved to: {favicon_path}")

    except FileNotFoundError:
        print(f"❌ Error: Source image not found at {SOURCE_IMAGE}")
        print("Please ensure haleway_square.png exists in static/img/")
    except Exception as e:
        print(f"❌ Error generating icons: {e}")

if __name__ == '__main__':
    generate_icons()
