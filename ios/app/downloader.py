"""
downloader.py — FFmpeg discovery and yt-dlp download logic.
Extracted verbatim from original main.py; behaviour is identical.

Public API
----------
fmt_bytes(n)          → human-readable size string
download_media(...)   → blocking download; raises on unrecoverable error
"""

import os
import shutil
import sys
import tempfile
import urllib.request
import zipfile

import yt_dlp
from yt_dlp.utils import DownloadCancelled  # re-exported for callers

from .constants import RES_FORMAT

# Module-level cache so FFmpeg is discovered only once per session.
_FFMPEG_LOCATION: str | None = None


# ── Utilities ─────────────────────────────────────────────────────────────────

def fmt_bytes(n: float) -> str:
    """Return a human-readable byte count string."""
    if not n:
        return "?"
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.2f} TB"


# ── FFmpeg discovery ──────────────────────────────────────────────────────────

def _get_ffmpeg_location() -> str | None:
    """
    Return the directory containing the ffmpeg binary, or None.

    Resolution order:
    1. Cached result from a previous call.
    2. System PATH.
    3. Common Windows app-data paths.
    4. Silent auto-download on Windows (desktop dev/testing only).
    """
    global _FFMPEG_LOCATION
    if _FFMPEG_LOCATION and os.path.exists(_FFMPEG_LOCATION):
        return _FFMPEG_LOCATION

    # 1. System PATH
    ffmpeg_bin = shutil.which("ffmpeg")
    if ffmpeg_bin:
        _FFMPEG_LOCATION = os.path.dirname(ffmpeg_bin)
        return _FFMPEG_LOCATION

    # 2. Windows-specific paths
    if sys.platform == "win32":
        ffmpeg_base = os.path.join(
            os.environ.get("LOCALAPPDATA", ""), "YTDownloader", "ffmpeg"
        )
        target_bin = os.path.join(ffmpeg_base, "bin")

        if os.path.exists(os.path.join(target_bin, "ffmpeg.exe")):
            _FFMPEG_LOCATION = target_bin
            return _FFMPEG_LOCATION

        common_paths = [
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "ffmpeg", "bin"),
            os.path.join(os.environ.get("APPDATA", ""), "ffmpeg", "bin"),
            os.path.join(os.path.dirname(sys.executable), "ffmpeg", "bin"),
            os.path.join(os.path.dirname(sys.argv[0]), "ffmpeg", "bin"),
        ]
        for path in common_paths:
            if os.path.exists(os.path.join(path, "ffmpeg.exe")):
                _FFMPEG_LOCATION = path
                return _FFMPEG_LOCATION

        # 3. Silent auto-download for Windows desktop testing
        try:
            os.makedirs(ffmpeg_base, exist_ok=True)
            ffmpeg_url = (
                "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/"
                "ffmpeg-master-latest-win64-gpl.zip"
            )
            temp_zip = os.path.join(tempfile.gettempdir(), "ffmpeg_ytdownloader.zip")
            urllib.request.urlretrieve(ffmpeg_url, temp_zip)

            extracted_dir = temp_zip.replace(".zip", "")
            with zipfile.ZipFile(temp_zip, "r") as zip_ref:
                zip_ref.extractall(extracted_dir)

            for item in os.listdir(extracted_dir):
                if "ffmpeg" in item.lower():
                    src_bin = os.path.join(extracted_dir, item, "bin")
                    if os.path.exists(src_bin):
                        if os.path.exists(target_bin):
                            shutil.rmtree(target_bin)
                        shutil.copytree(src_bin, target_bin)
                        _FFMPEG_LOCATION = target_bin
                        break

            if os.path.exists(temp_zip):
                os.remove(temp_zip)
            if os.path.exists(extracted_dir):
                shutil.rmtree(extracted_dir)

            return _FFMPEG_LOCATION
        except Exception:
            pass  # FFmpeg not critical on iOS (native codec path used)

    return None


# ── Download ──────────────────────────────────────────────────────────────────

def download_media(
    url: str,
    media_type: str,
    output_path: str,
    resolution: str = "720p",
    audio_format: str = "mp3",
    audio_quality: str = "192 kbps",
    progress_hook=None,
) -> None:
    """
    Download video (MP4) or audio from a YouTube URL.

    Parameters
    ----------
    url          : YouTube video URL.
    media_type   : ``"video"`` or ``"audio"``.
    output_path  : Directory where the file will be saved.
    resolution   : One of VIDEO_RESOLUTIONS (video mode only).
    audio_format : One of AUDIO_FORMATS (audio mode only).
    audio_quality: One of AUDIO_QUALITIES (audio mode only).
    progress_hook: Optional yt-dlp progress hook callable.

    Raises
    ------
    DownloadCancelled : If the hook raised it (user-initiated cancel).
    Any yt-dlp/network exception on unrecoverable failure.
    """
    ffmpeg_path = _get_ffmpeg_location()
    bitrate = audio_quality.replace(" kbps", "")

    base_opts: dict = {
        "socket_timeout"  : 30,
        "retries"         : 10,
        "fragment_retries": 10,
        "quiet"           : True,
        "no_warnings"     : True,
    }
    if ffmpeg_path:
        base_opts["ffmpeg_location"] = ffmpeg_path
    if progress_hook:
        base_opts["progress_hooks"] = [progress_hook]

    if media_type == "audio":
        tag = f"{audio_format.upper()} {bitrate}kbps"
        opts = {
            **base_opts,
            "outtmpl" : os.path.join(output_path, f"%(title)s [{tag}].%(ext)s"),
            "format"  : "bestaudio/best",
            "postprocessors": [
                {
                    "key"             : "FFmpegExtractAudio",
                    "preferredcodec"  : audio_format,
                    "preferredquality": bitrate,
                }
            ],
        }
    else:
        opts = {
            **base_opts,
            "outtmpl"            : os.path.join(
                output_path, f"%(title)s [{resolution}].%(ext)s"
            ),
            "format"             : RES_FORMAT.get(resolution, RES_FORMAT["720p"]),
            "merge_output_format": "mp4",
        }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
    except Exception as exc:
        # Fallback: if FFmpeg is absent on stock iOS, try native m4a
        is_audio_ffmpeg_error = media_type == "audio" and (
            "ffmpeg" in str(exc).lower() or "postprocessor" in str(exc).lower()
        )
        if is_audio_ffmpeg_error:
            fallback_opts = {
                **base_opts,
                "outtmpl": os.path.join(output_path, "%(title)s [audio].%(ext)s"),
                "format" : "bestaudio[ext=m4a]/bestaudio/best",
            }
            fallback_opts.pop("ffmpeg_location", None)
            with yt_dlp.YoutubeDL(fallback_opts) as ydl:
                ydl.download([url])
        else:
            raise
