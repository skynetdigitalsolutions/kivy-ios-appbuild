#!/usr/bin/env python3
"""
Generate iOS app icons from source image
"""

from PIL import Image
import os

# iOS app icon sizes (in pixels)
IOS_ICON_SIZES = [
    1024,  # App Store
    180,   # iPhone 60pt @3x
    167,   # iPad Pro 12.9" @2x
    152,   # iPad 76pt @2x
    120,   # iPhone 60pt @2x
    87,    # iPhone 29pt @3x
    80,    # iPhone 40pt @2x
    76,    # iPad 76pt @1x
    60,    # iPhone 60pt @1x
    58,    # iPhone 29pt @2x
    40,    # iPhone 40pt @1x
    29,    # iPhone 29pt @1x
    20,    # iPhone 20pt @2x
    16,    # iPhone 20pt @1x
]

def generate_icons(source_path, output_dir):
    """Generate iOS app icons from source image"""
    
    # Open source image
    try:
        img = Image.open(source_path)
        print(f"Loaded source image: {source_path}")
        print(f"Original size: {img.size}")
        
        # Convert to RGBA if necessary
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
            print("Converted to RGBA mode")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate icons for each size
        for size in IOS_ICON_SIZES:
            # Resize image
            resized = img.resize((size, size), Image.Resampling.LANCZOS)
            
            # Save as PNG
            output_path = os.path.join(output_dir, f"icon_{size}x{size}.png")
            resized.save(output_path, 'PNG')
            print(f"Generated: {output_path}")
        
        # Create the standard iOS icon set structure
        iconset_dir = os.path.join(output_dir, "AppIcon.appiconset")
        os.makedirs(iconset_dir, exist_ok=True)
        
        # Copy all generated PNGs into AppIcon.appiconset
        import shutil
        import glob
        for icon_file in glob.glob(os.path.join(output_dir, "icon_*.png")):
            shutil.copy(icon_file, iconset_dir)

        # Generate complete Contents.json for AppIcon.appiconset
        contents_json = {
          "images": [
            {"filename": "icon_20x20.png", "idiom": "iphone", "scale": "2x", "size": "20x20"},
            {"filename": "icon_60x60.png", "idiom": "iphone", "scale": "3x", "size": "20x20"},
            {"filename": "icon_29x29.png", "idiom": "iphone", "scale": "1x", "size": "29x29"},
            {"filename": "icon_58x58.png", "idiom": "iphone", "scale": "2x", "size": "29x29"},
            {"filename": "icon_87x87.png", "idiom": "iphone", "scale": "3x", "size": "29x29"},
            {"filename": "icon_40x40.png", "idiom": "iphone", "scale": "1x", "size": "40x40"},
            {"filename": "icon_80x80.png", "idiom": "iphone", "scale": "2x", "size": "40x40"},
            {"filename": "icon_120x120.png", "idiom": "iphone", "scale": "3x", "size": "40x40"},
            {"filename": "icon_60x60.png", "idiom": "iphone", "scale": "1x", "size": "60x60"},
            {"filename": "icon_120x120.png", "idiom": "iphone", "scale": "2x", "size": "60x60"},
            {"filename": "icon_180x180.png", "idiom": "iphone", "scale": "3x", "size": "60x60"},
            {"filename": "icon_76x76.png", "idiom": "ipad", "scale": "1x", "size": "76x76"},
            {"filename": "icon_152x152.png", "idiom": "ipad", "scale": "2x", "size": "76x76"},
            {"filename": "icon_167x167.png", "idiom": "ipad", "scale": "2x", "size": "83.5x83.5"},
            {"filename": "icon_1024x1024.png", "idiom": "ios-marketing", "scale": "1x", "size": "1024x1024"},
            {"filename": "icon_1024x1024.png", "idiom": "universal", "platform": "ios", "size": "1024x1024"}
          ],
          "info": {
            "author": "xcode",
            "version": 1
          }
        }
        
        import json
        with open(os.path.join(iconset_dir, "Contents.json"), 'w') as f:
            json.dump(contents_json, f, indent=2)
        
        print(f"\n[iOS app icons generated successfully!]")
        print(f"[Output directory: {output_dir}]")
        print(f"[AppIcon.appiconset created at: {iconset_dir}]")
        
    except Exception as e:
        print(f"[Error generating icons: {e}]")
        raise

if __name__ == "__main__":
    # Path to source favicon (project root directory)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ios_dir = os.path.dirname(script_dir)
    project_root = os.path.dirname(ios_dir)
    source_image = os.path.join(project_root, "favicon (1).ico")
    output_directory = script_dir

    print("iOS App Icon Generator")
    print("=" * 40)

    # Check if source exists
    if not os.path.exists(source_image):
        print(f"[Source image not found: {source_image}]")
        print("Please ensure 'favicon (1).ico' is in the project root directory")
        exit(1)

    generate_icons(source_image, output_directory)