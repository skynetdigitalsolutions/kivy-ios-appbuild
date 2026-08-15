"""
constants.py — App-wide constants: metadata, colours, download options.
All values extracted verbatim from original main.py to preserve behaviour.
"""

import os
from kivy.utils import get_color_from_hex

# ── App metadata ──────────────────────────────────────────────────────────────
APP_NAME      = "YT Downloader"
APP_VERSION   = os.environ.get("APP_VERSION", "v2.0.0")
DEV_NAME      = "Mpagi William & Tony Bbosa"
WHATSAPP_LINK = "https://chat.whatsapp.com/L1KGOt3d2A61Qh7UYwFBuF"

# ── Colour palette ────────────────────────────────────────────────────────────
BG       = get_color_from_hex("#0d1117")
SURFACE  = get_color_from_hex("#161b22")
SURF2    = get_color_from_hex("#21262d")
BORDER   = get_color_from_hex("#30363d")
ACCENT   = get_color_from_hex("#e94560")
ACCENT_H = get_color_from_hex("#c73652")
TEXT     = get_color_from_hex("#e6edf3")
SUBTEXT  = get_color_from_hex("#8b949e")
MUTED    = get_color_from_hex("#484f58")
SUCCESS  = get_color_from_hex("#3fb950")

# ── Download options ──────────────────────────────────────────────────────────
VIDEO_RESOLUTIONS = ["Best", "4K (2160p)", "1440p", "1080p", "720p", "480p", "360p"]
AUDIO_FORMATS     = ["mp3", "m4a", "aac", "opus", "wav"]
AUDIO_QUALITIES   = ["320 kbps", "256 kbps", "192 kbps", "128 kbps", "96 kbps", "64 kbps"]

# Maps resolution label → yt-dlp format selector
RES_FORMAT: dict[str, str] = {
    "Best"      : "bestvideo+bestaudio/best[ext=mp4]/best",
    "4K (2160p)": "bestvideo[height<=2160]+bestaudio/best[height<=2160][ext=mp4]/best",
    "1440p"     : "bestvideo[height<=1440]+bestaudio/best[height<=1440][ext=mp4]/best",
    "1080p"     : "bestvideo[height<=1080]+bestaudio/best[height<=1080][ext=mp4]/best",
    "720p"      : "bestvideo[height<=720]+bestaudio/best[height<=720][ext=mp4]/best",
    "480p"      : "bestvideo[height<=480]+bestaudio/best[height<=480][ext=mp4]/best",
    "360p"      : "bestvideo[height<=360]+bestaudio/best[height<=360][ext=mp4]/best",
}
