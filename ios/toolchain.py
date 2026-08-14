#!/usr/bin/env python3
"""
Custom toolchain configuration for YT Downloader iOS build
This extends the kivy-ios toolchain with app-specific settings
"""

import os
import sys

# App configuration
APP_TITLE = "YTDownloader"
APP_PACKAGE = "org.mpagiwilliam.ytdownloader"
APP_VERSION = "2.0.0"

# iOS build settings
IOS_MIN_VERSION = "12.0"
IOS_DEPLOYMENT_TARGET = "12.0"

# Dependencies that need to be compiled
RECIPIES_TO_BUILD = [
    "python3",
    "kivy",
    "ffmpeg",
]

# Pure Python dependencies (installed via pip)
PIP_PACKAGES = [
    "yt-dlp",
    "charset-normalizer>=3.0.0",
]

def get_toolchain_args():
    """Return custom arguments for toolchain commands"""
    return {
        "title": APP_TITLE,
        "package": APP_PACKAGE,
        "version": APP_VERSION,
        "ios_min_version": IOS_MIN_VERSION,
        "ios_deployment_target": IOS_DEPLOYMENT_TARGET,
    }

if __name__ == "__main__":
    print("YT Downloader iOS Toolchain Configuration")
    print(f"App: {APP_TITLE} v{APP_VERSION}")
    print(f"Package: {APP_PACKAGE}")
    print(f"iOS Target: {IOS_DEPLOYMENT_TARGET}+")
