#!/usr/bin/env python3
"""
generate_icons.py — Generate iOS app icons from a source image.

Usage (CLI):
    python generate_icons.py [--source PATH] [--output DIR]

Defaults:
    --source  <project_root>/favicon (1).ico
    --output  <this script's directory>
"""

import argparse
import glob
import json
import os
import shutil
from PIL import Image

# ── iOS app icon sizes (pixels) ───────────────────────────────────────────────
IOS_ICON_SIZES = [
    1024,  # App Store / Universal
    180,   # iPhone 60pt @3x
    167,   # iPad Pro 83.5pt @2x
    152,   # iPad 76pt @2x
    120,   # iPhone 40pt @3x / 60pt @2x
    87,    # iPhone 29pt @3x
    80,    # iPhone 40pt @2x
    76,    # iPad 76pt @1x
    60,    # iPhone 60pt @1x
    58,    # iPhone 29pt @2x
    40,    # iPhone 40pt @1x
    29,    # iPhone 29pt @1x
    20,    # iPhone 20pt @1x
]

# ── Contents.json template ────────────────────────────────────────────────────
CONTENTS_JSON = {
    "images": [
        {"filename": "icon_20x20.png",    "idiom": "iphone",       "scale": "2x", "size": "20x20"},
        {"filename": "icon_60x60.png",    "idiom": "iphone",       "scale": "3x", "size": "20x20"},
        {"filename": "icon_29x29.png",    "idiom": "iphone",       "scale": "1x", "size": "29x29"},
        {"filename": "icon_58x58.png",    "idiom": "iphone",       "scale": "2x", "size": "29x29"},
        {"filename": "icon_87x87.png",    "idiom": "iphone",       "scale": "3x", "size": "29x29"},
        {"filename": "icon_40x40.png",    "idiom": "iphone",       "scale": "1x", "size": "40x40"},
        {"filename": "icon_80x80.png",    "idiom": "iphone",       "scale": "2x", "size": "40x40"},
        {"filename": "icon_120x120.png",  "idiom": "iphone",       "scale": "3x", "size": "40x40"},
        {"filename": "icon_60x60.png",    "idiom": "iphone",       "scale": "1x", "size": "60x60"},
        {"filename": "icon_120x120.png",  "idiom": "iphone",       "scale": "2x", "size": "60x60"},
        {"filename": "icon_180x180.png",  "idiom": "iphone",       "scale": "3x", "size": "60x60"},
        {"filename": "icon_76x76.png",    "idiom": "ipad",         "scale": "1x", "size": "76x76"},
        {"filename": "icon_152x152.png",  "idiom": "ipad",         "scale": "2x", "size": "76x76"},
        {"filename": "icon_167x167.png",  "idiom": "ipad",         "scale": "2x", "size": "83.5x83.5"},
        {"filename": "icon_1024x1024.png","idiom": "ios-marketing", "scale": "1x", "size": "1024x1024"},
        {"filename": "icon_1024x1024.png","idiom": "universal",    "platform": "ios", "size": "1024x1024"},
    ],
    "info": {"author": "xcode", "version": 1},
}


# ── Core generator ────────────────────────────────────────────────────────────

def generate_icons(source_path: str, output_dir: str) -> None:
    """
    Generate iOS app icons from *source_path* into *output_dir*.

    Creates:
        <output_dir>/icon_NxN.png         for every size in IOS_ICON_SIZES
        <output_dir>/AppIcon.appiconset/  containing icons + Contents.json
    """
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Source image not found: {source_path}")

    img = Image.open(source_path)
    print(f"Loaded: {source_path}  ({img.size[0]}×{img.size[1]}  {img.mode})")

    if img.mode != "RGBA":
        img = img.convert("RGBA")
        print("Converted to RGBA.")

    os.makedirs(output_dir, exist_ok=True)

    # Generate all sizes
    for size in IOS_ICON_SIZES:
        resized = img.resize((size, size), Image.Resampling.LANCZOS)
        out_path = os.path.join(output_dir, f"icon_{size}x{size}.png")
        resized.save(out_path, "PNG")
        print(f"  → {out_path}")

    # Build AppIcon.appiconset
    iconset_dir = os.path.join(output_dir, "AppIcon.appiconset")
    os.makedirs(iconset_dir, exist_ok=True)

    for icon_file in glob.glob(os.path.join(output_dir, "icon_*.png")):
        shutil.copy(icon_file, iconset_dir)

    contents_path = os.path.join(iconset_dir, "Contents.json")
    with open(contents_path, "w", encoding="utf-8") as fh:
        json.dump(CONTENTS_JSON, fh, indent=2)

    print(f"\n✓ Icons generated in:      {output_dir}")
    print(f"✓ AppIcon.appiconset at:   {iconset_dir}")
    print(f"✓ Contents.json written:   {contents_path}")


# ── CLI entry point ───────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    script_dir   = os.path.dirname(os.path.abspath(__file__))
    ios_dir      = os.path.dirname(script_dir)
    project_root = os.path.dirname(ios_dir)

    parser = argparse.ArgumentParser(
        description="Generate iOS app icons from a source image."
    )
    parser.add_argument(
        "--source",
        default=os.path.join(project_root, "favicon (1).ico"),
        help="Path to the source image (default: <project_root>/favicon (1).ico)",
    )
    parser.add_argument(
        "--output",
        default=script_dir,
        help="Output directory (default: appicon/)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    print("iOS App Icon Generator")
    print("=" * 42)
    generate_icons(source_path=args.source, output_dir=args.output)