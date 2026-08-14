"""
main.py — YT Downloader Kivy App (iOS)
iOS-specific version of the main app with platform-specific handling.
Entry point for kivy-ios and iOS device testing.
"""

import os
import sys
import threading
import urllib.request
import webbrowser
import io
import traceback

try:
    import yt_dlp
    from yt_dlp.utils import DownloadCancelled
except ImportError:
    print("yt_dlp not available, install with: pip install yt-dlp")
    # Create a stub for graceful degradation
    class DownloadCancelled(Exception):
        pass

    class YoutubeDL:
        def __init__(self, opts):
            raise ImportError("yt-dlp is required but not installed")

from kivy.app import App
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.lang import Builder
from kivy.metrics import dp, sp
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex

# ── iOS detection ───────────────────────────────────────────────────────────
try:
    import platform
    IS_IOS = platform.system() == 'iOS' or 'IOS_ARGUMENT' in os.environ
except:
    IS_IOS = False

if IS_IOS:
    print("iOS detected - running on device")
else:
    print("Running on desktop")

# ── iOS runtime detection ───────────────────────────────────────────────────
def _is_ios_runtime():
    try:
        import platform
        return platform.system() == 'iOS' or "IOS_ARGUMENT" in os.environ
    except:
        return "IOS_ARGUMENT" in os.environ

# ── iOS permission handling ─────────────────────────────────────────────────
def check_request_permissions():
    """Request necessary iOS permissions at runtime."""
    if IS_IOS:
        try:
            # iOS uses a different permission model
            # Most permissions are handled via Info.plist and runtime dialogs
            # For file access, iOS uses app sandboxing
            print("iOS permissions handled via Info.plist and sandboxing")
            # Request network permission if needed (iOS 14+)
            try:
                from Foundation import NSBundle
                bundle = NSBundle.mainBundle()
                info = bundle.infoDictionary()
                print(f"App bundle info: {info}")
            except Exception as e:
                print(f"Bundle info check failed: {e}")
        except Exception as e:
            print(f"Permission check failed: {e}")

# ── Download logic ───────────────────────────────────────────────────────────────
VIDEO_RESOLUTIONS = ["Best", "4K (2160p)", "1440p", "1080p", "720p", "480p", "360p"]
AUDIO_FORMATS = ["mp3", "m4a", "aac", "opus", "wav"]
AUDIO_QUALITIES = ["320 kbps", "256 kbps", "192 kbps", "128 kbps", "96 kbps", "64 kbps"]

_RES_FORMAT = {
    "Best": "bestvideo+bestaudio/best",
    "4K (2160p)": "bestvideo[height<=2160]+bestaudio/best",
    "1440p": "bestvideo[height<=1440]+bestaudio/best",
    "1080p": "bestvideo[height<=1080]+bestaudio/best",
    "720p": "bestvideo[height<=720]+bestaudio/best",
    "480p": "bestvideo[height<=480]+bestaudio/best",
    "360p": "bestvideo[height<=360]+bestaudio/best",
}

# Add yt_dlp fallback for iOS without ffmpeg
def download_media_simple(url, media_type, output_path, resolution="720p", audio_format="mp3", audio_quality="192 kbps", progress_hook=None, cancel_check=None):
    """Simplified download function for iOS without ffmpeg."""
    bitrate = audio_quality.replace(" kbps", "")

    base = {
        "socket_timeout": 30,
        "retries": 10,
        "fragment_retries": 10,
        "noplaylist": True,
        "outtmpl": os.path.join(output_path, "%(title)s.%(ext)s"),
    }

    if progress_hook:
        def _progress_wrapper(d):
            if cancel_check and cancel_check():
                raise DownloadCancelled("Download cancelled by user.")
            if progress_hook:
                progress_hook(d)
        base["progress_hooks"] = [_progress_wrapper]

    if media_type == "audio":
        tag = f"{audio_format.upper()} {bitrate}kbps"
        opts = {
            **base,
            "outtmpl": os.path.join(output_path, f"%(title)s [{tag}].%(ext)s"),
            "format": "bestaudio/best",
        }
    else:
        opts = {
            **base,
            "outtmpl": os.path.join(output_path, f"%(title)s [{resolution}].%(ext)s"),
            "format": _RES_FORMAT.get(resolution, _RES_FORMAT["720p"]),
        }

    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])


def _get_ffmpeg_location():
    if _is_ios_runtime():
        # iOS specific paths for ffmpeg
        candidate_paths = [
            os.path.join(os.path.dirname(sys.executable), "ffmpeg"),
            "/usr/local/bin/ffmpeg",
        ]
        for path in candidate_paths:
            if os.path.exists(path):
                return path
        return None

    ffmpeg_names = ["ffmpeg.exe", "ffmpeg"]
    for search_dir in [os.path.dirname(sys.executable), os.path.dirname(sys.argv[0])]:
        if not search_dir:
            continue
        for name in ffmpeg_names:
            candidate = os.path.join(search_dir, name)
            if os.path.exists(candidate):
                return search_dir

    return None


def download_media(
    url: str,
    media_type: str,
    output_path: str = ".",
    resolution: str = "720p",
    audio_format: str = "mp3",
    audio_quality: str = "192 kbps",
    progress_hook=None,
):
    """Download video (MP4) or audio from a YouTube URL - iOS version."""
    ffmpeg_path = _get_ffmpeg_location()
    bitrate = audio_quality.replace(" kbps", "")

    # iOS-specific optimizations
    base = {
        "ffmpeg_location": ffmpeg_path,
        "socket_timeout": 60,  # Longer timeout for iOS network
        "retries": 15,  # More retries for iOS
        "fragment_retries": 15,
        "retry_sleep_functions": {"http": lambda n: min(5 * n, 45)},
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "nocheckcertificate": True,  # iOS certificate handling
        "no_cache": True,  # Reduce memory usage on iOS
    }

    if progress_hook:
        base["progress_hooks"] = [progress_hook]

    if media_type == "audio":
        tag = f"{audio_format.upper()} {bitrate}kbps"
        opts = {
            **base,
            "outtmpl": os.path.join(output_path, f"%(title)s [{tag}].%(ext)s"),
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": audio_format,
                    "preferredquality": bitrate,
                }
            ],
        }
    else:
        opts = {
            **base,
            "outtmpl": os.path.join(output_path, f"%(title)s [{resolution}].%(ext)s"),
            "format": _RES_FORMAT.get(resolution, _RES_FORMAT["720p"]),
            "merge_output_format": "mp4",
            "postprocessor_args": {
                "merger+ffmpeg_o": ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k"],
            },
        }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
    except Exception as e:
        print(f"Download error: {e}")
        raise


# ── Output path ─────────────────────────────────────────────────────────────────
def get_output_directory():
    """Get the appropriate output directory for the platform."""
    if IS_IOS:
        try:
            # iOS uses app sandboxing
            # Get the app's Documents directory
            from Foundation import NSDocumentDirectory, NSSearchPathForDirectoriesInDomains, NSUserDomainMask
            paths = NSSearchPathForDirectoriesInDomains(NSDocumentDirectory, NSUserDomainMask, True)
            if paths and len(paths) > 0:
                out_dir = os.path.join(paths[0], "YTDownloader")
                print(f"iOS Documents directory: {out_dir}")
            else:
                # Fallback
                out_dir = os.path.join(os.path.expanduser("~"), "Documents", "YTDownloader")
                print(f"iOS fallback directory: {out_dir}")
        except ImportError:
            # Foundation not available (desktop testing)
            print("Foundation not available, using desktop path")
            out_dir = os.path.join(os.path.expanduser("~"), "Downloads", "YTDownloader")
        except Exception as e:
            # Fallback for desktop testing
            print(f"iOS directory access failed: {e}, using fallback")
            out_dir = os.path.join(os.path.expanduser("~"), "Downloads", "YTDownloader")
    else:
        out_dir = os.path.join(os.path.expanduser("~"), "Downloads", "YTDownloader")
        print(f"Desktop output directory: {out_dir}")

    # Create directory if it doesn't exist
    try:
        os.makedirs(out_dir, exist_ok=True)
        print(f"Output directory created/verified: {out_dir}")
    except Exception as e:
        print(f"Warning: Could not create output directory: {e}")
        # Fallback to current directory
        out_dir = "."
        print(f"Using fallback directory: {out_dir}")

    return out_dir

OUT_DIR = get_output_directory()
print(f"Output directory: {OUT_DIR}")

# ── Branding ────────────────────────────────────────────────────────────────────
APP_NAME = "YT Downloader"
APP_VERSION = "2.0.0"
DEV_NAMES = ["Mpagi William", "Tong Bbosa"]
DEV_ROLE = "Full-Stack Developers"
DEV_CONTACT = "skynetdigitalsolutionsug@gmail.com"

# ── Ad config — swap these to change the ad ─────────────────────────────────────
AD_IMAGE_URL = ""   # e.g. "https://yourcdn.com/banner.png"
AD_CLICK_URL = ""   # e.g. "https://your-sponsor.com"

# ── Colour palette (exact match with app.py) ────────────────────────────────────
BG       = get_color_from_hex("#0d1117")
SURFACE  = get_color_from_hex("#161b22")
SURF2    = get_color_from_hex("#21262d")
BORDER   = get_color_from_hex("#30363d")
ACCENT   = get_color_from_hex("#e94560")
ACCENT_H = get_color_from_hex("#c73652")
TEXT     = get_color_from_hex("#e6edf3")
SUBTEXT  = get_color_from_hex("#8b949e")
MUTED    = get_color_from_hex("#484f58")

# ── KV rules (reusable widget styles) ──────────────────────────────────────────
Builder.load_string("""
#:import dp  kivy.metrics.dp
#:import sp  kivy.metrics.sp
#:import hex kivy.utils.get_color_from_hex

<SecLabel@Label>:
    font_size:    sp(10)
    bold:         True
    color:        hex('#8b949e')
    size_hint_y:  None
    height:       dp(26)
    halign:       'left'
    valign:       'bottom'
    text_size:    self.width, None

<DivLine@Widget>:
    size_hint_y: None
    height: dp(1)
    canvas:
        Color:
            rgba: hex('#30363d')
        Rectangle:
            pos:  self.pos
            size: self.size
""")


# ═══════════════════════════════════════════════════════════════════════════════
#  Styled Progress Bar Widget
# ═══════════════════════════════════════════════════════════════════════════════

class StyledBar(Widget):
    value = NumericProperty(0)
    max = NumericProperty(100)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(10)

        # Background
        with self.canvas.before:
            self.bg_color = Color(*SURF2)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(5)])

        # Progress bar
        with self.canvas:
            self.fg_color = Color(*ACCENT)
            self.fg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(5)])

        self.bind(pos=self._update_rects, size=self._update_rects, value=self._update_progress)

    def _update_rects(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self._update_progress()

    def _update_progress(self, *args):
        if self.max > 0:
            progress_width = self.width * (self.value / self.max)
        else:
            progress_width = 0
        self.fg_rect.pos = self.pos
        self.fg_rect.size = (progress_width, self.height)


# ═══════════════════════════════════════════════════════════════════════════════
#  Widget helpers
# ═══════════════════════════════════════════════════════════════════════════════


def _attach_bg(widget, color, radius=0):
    """Attach a live background rect (or rounded rect) to any widget."""
    with widget.canvas.before:
        clr = Color(*color)
        if radius:
            rect = RoundedRectangle(
                pos=widget.pos, size=widget.size, radius=[dp(radius)]
            )
        else:
            rect = Rectangle(pos=widget.pos, size=widget.size)
    widget.bind(
        pos=lambda *_: setattr(rect, "pos", widget.pos),
        size=lambda *_: setattr(rect, "size", widget.size),
    )
    return clr, rect


def _swap_bg(widget, color, radius=8):
    """Clear and re-attach a rounded background (for button state changes)."""
    widget.canvas.before.clear()
    _attach_bg(widget, color, radius)


def make_label(text, font_size=14, color=None, bold=False, height=None, halign="left"):
    lbl = Label(
        text=text,
        font_size=sp(font_size),
        bold=bold,
        color=color or TEXT,
        size_hint_y=None if height else 1,
        height=dp(height) if height else 0,
        halign=halign,
        valign="middle",
    )
    lbl.bind(size=lambda *_: setattr(lbl, "text_size", (lbl.width, None)))
    return lbl


def make_input(hint=""):
    return TextInput(
        hint_text=hint,
        hint_text_color=MUTED,
        background_color=SURF2,
        foreground_color=TEXT,
        cursor_color=ACCENT,
        font_size=sp(14),
        padding=[dp(12), dp(10)],
        size_hint_y=None,
        height=dp(48),
        multiline=False,
    )


def make_button(text, bg=SURF2, fg=SUBTEXT, height=48, font_size=12, bold=True, radius=8):
    btn = Button(
        text=text,
        color=fg,
        font_size=sp(font_size),
        bold=bold,
        background_color=(0, 0, 0, 0),
        background_normal="",
        size_hint_y=None,
        height=dp(height),
    )
    _attach_bg(btn, bg, radius)

    def _on_state(inst, val):
        _swap_bg(inst, ACCENT_H if val == "down" else bg, radius)

    btn.bind(state=_on_state)
    return btn


def make_accent_btn(text, height=54, font_size=14):
    return make_button(
        text, bg=ACCENT, fg=TEXT, height=height, font_size=font_size, bold=True
    )


def make_spinner(values, default, height=46):
    spn = Spinner(
        text=default,
        values=values,
        background_color=(0, 0, 0, 0),
        background_normal="",
        color=TEXT,
        font_size=sp(13),
        size_hint_y=None,
        height=dp(height),
    )
    _attach_bg(spn, SURF2, radius=8)
    return spn


def make_seg_button(text, group, height=46):
    """Segmented-control button (like the Tkinter toggle pair)."""
    tb = ToggleButton(
        text=text,
        group=group,
        background_color=(0, 0, 0, 0),
        background_normal="",
        background_down="",
        color=TEXT,
        font_size=sp(12),
        bold=True,
        size_hint_y=None,
        height=dp(height),
    )
    _attach_bg(tb, SURF2, radius=8)

    def _on_state(inst, val):
        _swap_bg(inst, ACCENT if val == "down" else SURF2, radius=8)

    tb.bind(state=_on_state)
    return tb


def fmt_bytes(n):
    """Format bytes to human-readable string."""
    if not n:
        return "?"
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.2f} TB"


# ═══════════════════════════════════════════════════════════════════════════════
#  Popup helper (replaces messagebox from Tkinter)
# ═══════════════════════════════════════════════════════════════════════════════


def show_popup(title, message):
    """Show a Kivy popup dialog (info, warning, or error)."""
    box = BoxLayout(
        orientation="vertical",
        padding=[dp(20), dp(16)],
        spacing=dp(12),
        size_hint=(None, None),
        size=(dp(320), dp(180)),
    )
    _attach_bg(box, SURFACE, radius=12)

    lbl = Label(
        text=str(message),
        font_size=sp(13),
        color=TEXT,
        halign="center",
        valign="middle",
        size_hint_y=None,
        height=dp(80),
    )
    lbl.bind(size=lambda *_: setattr(lbl, "text_size", (lbl.width, None)))
    box.add_widget(lbl)

    ok_btn = make_accent_btn("OK", height=44, font_size=13)
    popup = Popup(
        title=title,
        title_size=sp(15),
        title_color=TEXT,
        separator_color=ACCENT,
        content=box,
        size_hint=(None, None),
        size=(dp(340), dp(200)),
        auto_dismiss=True,
        background_color=(0, 0, 0, 0),
    )

    def dismiss(*_):
        popup.dismiss()

    ok_btn.bind(on_release=dismiss)
    box.add_widget(ok_btn)
    popup.open()


# ═══════════════════════════════════════════════════════════════════════════════
#  Main layout — faithful replica of the Tkinter app.py UI
# ═══════════════════════════════════════════════════════════════════════════════


class YTDownloaderLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        _attach_bg(self, BG)
        self._media_type = "video"  # Default to video
        self._cancel_flag = threading.Event()
        self._current_thread = None

        # Request iOS permissions
        check_request_permissions()

        print("Building UI...")
        self._build()
        print("UI built successfully")

    # ══════════════════════════════════════════════════════════════════════════
    #  Build
    # ══════════════════════════════════════════════════════════════════════════

    def _build(self):
        self._build_header()
        self._build_body()
        self._build_ad_banner()
        self._build_footer()

    # ══════════════════════════════════════════════════════════════════════════
    #  Header — Red accent bar with icon, title, subtitle, version badge
    # ══════════════════════════════════════════════════════════════════════════

    def _build_header(self):
        hdr = BoxLayout(
            size_hint_y=None, height=dp(60), padding=[dp(18), 0], spacing=dp(10)
        )
        _attach_bg(hdr, ACCENT)

        # Left side — icon + title + subtitle
        left = BoxLayout(orientation="horizontal", spacing=dp(10))
        left.size_hint_x = None
        left.width = dp(200)

        icon = make_label("▶", font_size=22, color=TEXT, bold=True, height=60)
        icon.size_hint_x = None
        icon.width = dp(32)
        left.add_widget(icon)

        info = BoxLayout(orientation="vertical", padding=[0, dp(8), 0, dp(10)])
        info.add_widget(
            make_label(APP_NAME, font_size=15, color=TEXT, bold=True, height=24)
        )
        info.add_widget(
            make_label(
                "Fast  •  Simple  •  Reliable",
                font_size=9,
                color=(1, 1, 1, 0.6),
                height=16,
            )
        )
        left.add_widget(info)
        hdr.add_widget(left)

        # Right side — version badge (dark red pill)
        badge = BoxLayout(
            size_hint_x=None,
            size_hint_y=None,
            width=dp(50),
            height=dp(28),
            padding=[dp(10), dp(4)],
        )
        _attach_bg(badge, ACCENT_H, radius=4)
        badge_text = Label(
            text=APP_VERSION,
            font_size=sp(8),
            bold=True,
            color=TEXT,
            halign="center",
            valign="middle",
        )
        badge.add_widget(badge_text)

        # Right-align wrapper
        right = BoxLayout(size_hint_x=None, width=dp(70))
        right.add_widget(Widget())  # spacer
        right.add_widget(badge)
        hdr.add_widget(right)

        self.add_widget(hdr)

    # ══════════════════════════════════════════════════════════════════════════
    #  Body — scrollable content area
    # ══════════════════════════════════════════════════════════════════════════

    def _build_body(self):
        scroll = ScrollView(do_scroll_x=False)
        _attach_bg(scroll, SURFACE)

        self._box = BoxLayout(
            orientation="vertical",
            padding=[dp(20), dp(16)],
            spacing=dp(10),
            size_hint_y=None,
        )
        self._box.bind(minimum_height=self._box.setter("height"))
        _attach_bg(self._box, SURFACE)

        self._sec_url()
        self._sec_type()
        self._sec_options()

        # Divider line
        divider = Widget(size_hint_y=None, height=dp(1))
        with divider.canvas.before:
            Color(*BORDER)
            r = Rectangle(pos=divider.pos, size=divider.size)
        divider.bind(
            pos=lambda *_: setattr(r, "pos", divider.pos),
            size=lambda *_: setattr(r, "size", divider.size),
        )
        self._box.add_widget(divider)

        self._sec_save()
        self._sec_download()
        self._sec_progress()

        scroll.add_widget(self._box)
        self.add_widget(scroll)

    def _add(self, w):
        self._box.add_widget(w)

    # ══════════════════════════════════════════════════════════════════════════
    #  URL Section
    # ══════════════════════════════════════════════════════════════════════════

    def _sec_url(self):
        self._add(make_label("YouTube URL", font_size=10, color=SUBTEXT, bold=True))

        url_box = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(46))

        self._url_input = make_input("Paste YouTube link here...")
        url_box.add_widget(self._url_input)

        paste_btn = make_button("Paste", fg=TEXT, height=46, font_size=11)

        def on_paste(instance):
            try:
                clipboard_content = Clipboard.paste()
                if clipboard_content:
                    self._url_input.text = clipboard_content
                    print(f"Pasted: {clipboard_content}")
                else:
                    show_popup("Info", "Clipboard is empty")
            except Exception as e:
                print(f"Paste error: {e}")
                show_popup("Error", "Could not access clipboard")

        paste_btn.bind(on_release=on_paste)
        url_box.add_widget(paste_btn)

        self._add(url_box)

    # ══════════════════════════════════════════════════════════════════════════
    #  Media Type Section
    # ══════════════════════════════════════════════════════════════════════════

    def _sec_type(self):
        self._add(make_label("Media Type", font_size=10, color=SUBTEXT, bold=True))

        type_box = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(46))
        self._video_btn = make_seg_button("Video (MP4)", "mediatype", height=46)
        self._audio_btn = make_seg_button("Audio Only", "mediatype", height=46)

        type_box.add_widget(self._video_btn)
        type_box.add_widget(self._audio_btn)

        # Set default selection to Video (first button added)
        self._video_btn.state = "down"

        def on_type_change(btn, value):
            if value == "down":
                self._media_type = "video" if btn == self._video_btn else "audio"
                print(f"Media type changed to: {self._media_type}")
                self._swap_opts()

        self._video_btn.bind(state=on_type_change)
        self._audio_btn.bind(state=on_type_change)

        self._add(type_box)

    # ══════════════════════════════════════════════════════════════════════════
    #  Options Section
    # ══════════════════════════════════════════════════════════════════════════

    def _sec_options(self):
        self._add(make_label("Quality Options", font_size=10, color=SUBTEXT, bold=True))

        # Container for swapping options
        self._options_container = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(110), spacing=dp(12))

        # Video options
        self._video_opts = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(60), spacing=dp(6))
        res_label = make_label("Resolution", font_size=9, color=MUTED, height=20)
        self._res_spinner = make_spinner(VIDEO_RESOLUTIONS, "720p")
        self._video_opts.add_widget(res_label)
        self._video_opts.add_widget(self._res_spinner)

        # Audio options
        self._audio_opts = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(100), spacing=dp(12))

        # Audio format row
        fmt_row = BoxLayout(orientation="horizontal", spacing=dp(12), size_hint_y=None, height=dp(44))
        fmt_label = make_label("Format", font_size=9, color=MUTED, height=44)
        self._fmt_spinner = make_spinner(AUDIO_FORMATS, "mp3")
        fmt_row.add_widget(fmt_label)
        fmt_row.add_widget(self._fmt_spinner)

        # Audio quality row
        qual_row = BoxLayout(orientation="horizontal", spacing=dp(12), size_hint_y=None, height=dp(44))
        qual_label = make_label("Quality", font_size=9, color=MUTED, height=44)
        self._qual_spinner = make_spinner(AUDIO_QUALITIES, "192 kbps")
        qual_row.add_widget(qual_label)
        qual_row.add_widget(self._qual_spinner)

        self._audio_opts.add_widget(fmt_row)
        self._audio_opts.add_widget(qual_row)

        # Initially show video options
        self._options_container.add_widget(self._video_opts)
        self._add(self._options_container)

    def _swap_opts(self):
        """Swap between video and audio options based on media type."""
        self._options_container.clear_widgets()
        if self._media_type == "video":
            self._options_container.add_widget(self._video_opts)
        else:
            self._options_container.add_widget(self._audio_opts)

    # ══════════════════════════════════════════════════════════════════════════
    #  Save Location Section
    # ══════════════════════════════════════════════════════════════════════════

    def _sec_save(self):
        self._add(make_label("Save Location", font_size=10, color=SUBTEXT, bold=True))

        location_box = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(46))

        self._location_label = make_input(OUT_DIR)
        self._location_label.readonly = True
        location_box.add_widget(self._location_label)

        browse_btn = make_button("Browse", fg=TEXT, height=46, font_size=11)

        def on_browse(instance):
            # On iOS, file browsing is limited
            if IS_IOS:
                show_popup("Info", "On iOS, files are saved to the app's Documents directory automatically.")
            else:
                show_popup("Info", f"Files will be saved to:\n{OUT_DIR}")

        browse_btn.bind(on_release=on_browse)
        location_box.add_widget(browse_btn)

        self._add(location_box)

    # ══════════════════════════════════════════════════════════════════════════
    #  Download Section
    # ══════════════════════════════════════════════════════════════════════════

    def _sec_download(self):
        # Create button row for side-by-side layout
        button_row = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(54))

        self._download_btn = make_accent_btn("⬇   DOWNLOAD", height=54, font_size=12)
        self._download_btn.size_hint_x = 0.75  # Download button takes 75% of space
        self._download_btn.bind(on_release=self._on_download)
        button_row.add_widget(self._download_btn)

        self._cancel_btn = make_button("✖   CANCEL", bg=BORDER, fg=TEXT, height=54, font_size=12)
        self._cancel_btn.size_hint_x = 0.25  # Cancel button takes 25% of space
        self._cancel_btn.disabled = True
        self._cancel_btn.bind(on_release=self._on_cancel)
        button_row.add_widget(self._cancel_btn)

        self._add(button_row)

    # ══════════════════════════════════════════════════════════════════════════
    #  Progress Section
    # ══════════════════════════════════════════════════════════════════════════

    def _sec_progress(self):
        self._add(make_label("Download Progress", font_size=10, color=SUBTEXT, bold=True))
        
        self._progress_bar = StyledBar(value=0, max=100)
        self._add(self._progress_bar)
        
        self._progress_label = make_label("Ready to download", font_size=11, color=MUTED, height=20)
        self._add(self._progress_label)

    # ══════════════════════════════════════════════════════════════════════════
    #  Ad Banner Section
    # ══════════════════════════════════════════════════════════════════════════

    def _build_ad_banner(self):
        if AD_IMAGE_URL and AD_CLICK_URL:
            ad_container = BoxLayout(
                orientation="vertical",
                size_hint_y=None,
                height=dp(80),
                padding=[dp(20), 0],
            )
            
            ad_label = make_label("Sponsored", font_size=8, color=MUTED, height=16)
            ad_container.add_widget(ad_label)
            
            # Here you would add an async image loader for the ad
            # For now, just a placeholder
            ad_placeholder = make_label("Ad Space", font_size=10, color=BORDER, height=dp(60))
            ad_container.add_widget(ad_placeholder)
            
            self.add_widget(ad_container)

    # ══════════════════════════════════════════════════════════════════════════
    #  Footer Section
    # ══════════════════════════════════════════════════════════════════════════

    def _build_footer(self):
        footer = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(60),
            padding=[dp(20), dp(10)],
            spacing=dp(4),
        )
        _attach_bg(footer, BG)

        dev_info = make_label(
            f"Developed by {', '.join(DEV_NAMES)}",
            font_size=9,
            color=MUTED,
            height=16,
            halign="center"
        )
        footer.add_widget(dev_info)

        contact_info = make_label(
            DEV_CONTACT,
            font_size=8,
            color=BORDER,
            height=16,
            halign="center"
        )
        footer.add_widget(contact_info)

        version_info = make_label(
            f"Version {APP_VERSION} • iOS Edition",
            font_size=8,
            color=BORDER,
            height=16,
            halign="center"
        )
        footer.add_widget(version_info)

        self.add_widget(footer)

    # ══════════════════════════════════════════════════════════════════════════
    #  Download Handling
    # ══════════════════════════════════════════════════════════════════════════

    def _on_download(self, instance):
        url = self._url_input.text.strip()
        if not url:
            show_popup("Error", "Please enter a YouTube URL")
            return

        if not url.startswith(("http://", "https://")):
            show_popup("Error", "Please enter a valid URL")
            return

        # Disable download button, enable cancel
        self._download_btn.disabled = True
        self._cancel_btn.disabled = False
        self._cancel_flag.clear()

        # Start download in background thread
        self._current_thread = threading.Thread(
            target=self._run_download,
            args=(url,),
            daemon=True,
            name="DownloadThread"
        )
        self._current_thread.start()
        print(f"Download thread started for URL: {url}")

    def _on_cancel(self, instance):
        if self._current_thread and self._current_thread.is_alive():
            self._cancel_flag.set()
            print("Download cancellation requested")
            show_popup("Info", "Download cancelled")
        else:
            print("No active download to cancel")

    def _run_download(self, url):
        try:
            def progress_hook(d):
                if self._cancel_flag.is_set():
                    raise DownloadCancelled("Download cancelled by user.")

                if d["status"] == "downloading":
                    total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                    done = d.get("downloaded_bytes", 0)
                    speed = d.get("_speed_str", "").strip()
                    eta = d.get("_eta_str", "").strip()

                    size_str = (
                        f"{fmt_bytes(done)} / {fmt_bytes(total)}"
                        if total
                        else fmt_bytes(done)
                    )
                    parts = [size_str]
                    if speed:
                        parts.append(speed)
                    if eta:
                        parts.append(f"ETA {eta}")

                    if total:
                        pct = done / total * 100
                        Clock.schedule_once(
                            lambda dt: self._update_progress(
                                pct,
                                f"Downloading…  {pct:.1f}% - {'   •   '.join(parts)}"
                            )
                        )
                    else:
                        Clock.schedule_once(
                            lambda dt: self._update_progress(
                                0,
                                f"Downloading… - {'   •   '.join(parts)}"
                            )
                        )

                elif d["status"] == "finished":
                    Clock.schedule_once(
                        lambda dt: self._update_progress(100, "Finalising…")
                    )

            download_media(
                url=url,
                media_type=self._media_type,
                output_path=OUT_DIR,
                resolution=self._res_spinner.text,
                audio_format=self._fmt_spinner.text,
                audio_quality=self._qual_spinner.text,
                progress_hook=progress_hook,
            )

            Clock.schedule_once(
                lambda dt: self._download_complete(None)
            )

        except DownloadCancelled:
            Clock.schedule_once(
                lambda dt: self._download_cancelled()
            )
        except Exception as e:
            error_msg = f"Download failed: {str(e)}"
            print(f"Error: {error_msg}")
            print(f"Traceback: {traceback.format_exc()}")
            Clock.schedule_once(
                lambda dt: self._download_complete(error_msg)
            )

    def _update_progress(self, progress, message):
        self._progress_bar.value = progress
        self._progress_label.text = message

    def _download_complete(self, error):
        self._download_btn.disabled = False
        self._cancel_btn.disabled = True

        if error:
            show_popup("Error", error)
            self._progress_label.text = f"✖   {error[:90]}"
        else:
            completion_message = "Audio download complete. Your file has been saved successfully." if self._media_type == "audio" else "Video download complete. Your file has been saved successfully."
            show_popup("Success", completion_message)
            self._progress_label.text = "✔   Download complete!"
            self._progress_bar.value = 100

    def _download_cancelled(self):
        self._download_btn.disabled = False
        self._cancel_btn.disabled = True
        self._progress_label.text = "✖   Download cancelled"
        self._progress_bar.value = 0


# ═══════════════════════════════════════════════════════════════════════════════
#  App Entry Point
# ═══════════════════════════════════════════════════════════════════════════════

class YTDownloaderApp(App):
    def build(self):
        return YTDownloaderLayout()

    def on_start(self):
        print(f"YT Downloader iOS v{APP_VERSION} starting...")
        print(f"Platform: {'iOS' if IS_IOS else 'Desktop'}")

    def on_stop(self):
        print("YT Downloader iOS stopping...")


if __name__ == "__main__":
    YTDownloaderApp().run()
