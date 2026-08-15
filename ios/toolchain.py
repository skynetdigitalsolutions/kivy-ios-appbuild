#!/usr/bin/env python3
"""
toolchain.py — kivy-ios toolchain configuration for YT Downloader.

APP_VERSION is read from the APP_VERSION environment variable so CI can
inject the version from the workflow dispatch input without editing this file.
"""

import os

# ── App configuration ─────────────────────────────────────────────────────────
APP_TITLE   = "YTDownloader"
APP_PACKAGE = "org.mpagiwilliam.ytdownloader"

# Single source of truth: injected by CI via env var; falls back to default.
APP_VERSION = os.environ.get("APP_VERSION", "2.0.0")

# ── iOS build settings ────────────────────────────────────────────────────────
IOS_MIN_VERSION        = "12.0"
IOS_DEPLOYMENT_TARGET  = "12.0"

# ── Recipes to compile (via kivy-ios toolchain) ───────────────────────────────
RECIPES_TO_BUILD = [
    "hostpython3",
    "python3",
    "kivy",
    "ffmpeg",
]

# ── Pure-Python packages (installed via toolchain pip) ────────────────────────
# Do NOT add 'kivy' or 'pyobjus' — they are handled by the toolchain recipes.
PIP_PACKAGES = [
    "yt-dlp",
    "charset-normalizer>=3.0.0",
    "plyer",
]


def get_toolchain_args() -> dict:
    """Return custom arguments for toolchain commands."""
    return {
        "title"                : APP_TITLE,
        "package"              : APP_PACKAGE,
        "version"              : APP_VERSION,
        "ios_min_version"      : IOS_MIN_VERSION,
        "ios_deployment_target": IOS_DEPLOYMENT_TARGET,
    }


if __name__ == "__main__":
    print("YT Downloader — iOS Toolchain Configuration")
    print(f"  App     : {APP_TITLE} v{APP_VERSION}")
    print(f"  Package : {APP_PACKAGE}")
    print(f"  iOS     : {IOS_DEPLOYMENT_TARGET}+")
    print(f"  Recipes : {', '.join(RECIPES_TO_BUILD)}")
