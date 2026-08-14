"""
YT Downloader – Kivy iOS Edition
Authors : Mpagi William & Tony Bbosa  (skynetdigitalsolutionsug@gmail.com)
Version : 2.0.0
"""

# ── Standard library ──────────────────────────────────────────────────────────
import os
import shutil
import sys
import tempfile
import threading
import time
import urllib.request
import zipfile

# ── yt-dlp ────────────────────────────────────────────────────────────────────
import yt_dlp
from yt_dlp.utils import DownloadCancelled

# ── Kivy ──────────────────────────────────────────────────────────────────────
from kivy.app import App
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import (
    BooleanProperty,
    ColorProperty,
    NumericProperty,
    StringProperty,
)
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.utils import get_color_from_hex

# ── App metadata ──────────────────────────────────────────────────────────────
APP_NAME    = "YT Downloader"
APP_VERSION = "v2.0.0"
DEV_NAME    = "Mpagi William & Tony Bbosa"
DEV_ROLE    = "Full-Stack Developers"
DEV_CONTACT = "skynetdigitalsolutionsug@gmail.com"

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

_RES_FORMAT = {
    "Best"      : "bestvideo+bestaudio/best[ext=mp4]/best",
    "4K (2160p)": "bestvideo[height<=2160]+bestaudio/best[height<=2160][ext=mp4]/best",
    "1440p"     : "bestvideo[height<=1440]+bestaudio/best[height<=1440][ext=mp4]/best",
    "1080p"     : "bestvideo[height<=1080]+bestaudio/best[height<=1080][ext=mp4]/best",
    "720p"      : "bestvideo[height<=720]+bestaudio/best[height<=720][ext=mp4]/best",
    "480p"      : "bestvideo[height<=480]+bestaudio/best[height<=480][ext=mp4]/best",
    "360p"      : "bestvideo[height<=360]+bestaudio/best[height<=360][ext=mp4]/best",
}


# ── Utility ───────────────────────────────────────────────────────────────────
def fmt_bytes(n: float) -> str:
    if not n:
        return "?"
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.2f} TB"


FFMPEG_LOCATION = None


def _get_ffmpeg_location():
    """Get FFmpeg location if available, or automatically download for Windows desktop testing."""
    global FFMPEG_LOCATION
    if FFMPEG_LOCATION and os.path.exists(FFMPEG_LOCATION):
        return FFMPEG_LOCATION

    # 1. System PATH check
    ffmpeg_bin = shutil.which("ffmpeg")
    if ffmpeg_bin:
        FFMPEG_LOCATION = os.path.dirname(ffmpeg_bin)
        return FFMPEG_LOCATION

    # 2. Check local app / AppData paths if on Windows
    if sys.platform == "win32":
        ffmpeg_base = os.path.join(os.environ.get("LOCALAPPDATA", ""), "YTDownloader", "ffmpeg")
        target_bin = os.path.join(ffmpeg_base, "bin")
        if os.path.exists(os.path.join(target_bin, "ffmpeg.exe")):
            FFMPEG_LOCATION = target_bin
            return FFMPEG_LOCATION

        common_paths = [
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "ffmpeg", "bin"),
            os.path.join(os.environ.get("APPDATA", ""), "ffmpeg", "bin"),
            os.path.join(os.path.dirname(sys.executable), "ffmpeg", "bin"),
            os.path.join(os.path.dirname(sys.argv[0]), "ffmpeg", "bin"),
        ]
        for path in common_paths:
            if os.path.exists(os.path.join(path, "ffmpeg.exe")):
                FFMPEG_LOCATION = path
                return FFMPEG_LOCATION

        # 3. Silent automatic background download for Windows desktop testing
        try:
            os.makedirs(ffmpeg_base, exist_ok=True)
            ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
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
                        FFMPEG_LOCATION = target_bin
                        break

            if os.path.exists(temp_zip):
                os.remove(temp_zip)
            if os.path.exists(extracted_dir):
                shutil.rmtree(extracted_dir)

            return FFMPEG_LOCATION
        except Exception:
            pass

    return None


def download_media(
    url: str,
    media_type: str,
    output_path: str,
    resolution: str = "720p",
    audio_format: str = "mp3",
    audio_quality: str = "192 kbps",
    progress_hook=None,
):
    """Download video (MP4) or audio from YouTube URL."""
    ffmpeg_path = _get_ffmpeg_location()
    bitrate = audio_quality.replace(" kbps", "")
    base_opts = {
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
            "outtmpl": os.path.join(output_path, f"%(title)s [{tag}].%(ext)s"),
            "format" : "bestaudio/best",
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
            **base_opts,
            "outtmpl": os.path.join(
                output_path, f"%(title)s [{resolution}].%(ext)s"
            ),
            "format" : _RES_FORMAT.get(resolution, _RES_FORMAT["720p"]),
            "merge_output_format": "mp4",
        }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
    except Exception as e:
        # Fallback if FFmpeg is missing (e.g. on stock iOS without FFmpeg binary) when extracting audio
        if media_type == "audio" and ("ffmpeg" in str(e).lower() or "postprocessor" in str(e).lower()):
            fallback_opts = {
                **base_opts,
                "outtmpl": os.path.join(output_path, f"%(title)s [audio].%(ext)s"),
                "format" : "bestaudio[ext=m4a]/bestaudio/best",
            }
            if "ffmpeg_location" in fallback_opts:
                del fallback_opts["ffmpeg_location"]
            with yt_dlp.YoutubeDL(fallback_opts) as ydl:
                ydl.download([url])
        else:
            raise


# ── KV layout string ─────────────────────────────────────────────────────────
# NOTE: Builder.load_string() is called inside YTDownloaderApp.build() so that
#       dp() is resolved after the Kivy window/metrics are initialised.
KV = r"""
#:import get_color_from_hex kivy.utils.get_color_from_hex

<StyledButton>:
    canvas.before:
        Color:
            rgba: self.press_color if self.state == 'down' else self.bg_color
        RoundedRectangle:
            pos:    self.pos
            size:   self.size
            radius: [dp(10)]
    Label:
        text:      root.btn_text
        font_size: root.font_size
        color:     root.text_color
        bold:      True
        halign:    'center'
        valign:    'middle'
        text_size: self.size

<DividerLine>:
    size_hint_y: None
    height: dp(1)
    canvas.before:
        Color:
            rgba: get_color_from_hex('#30363d')
        Rectangle:
            pos:  self.pos
            size: self.size
"""


# ── Custom widgets ─────────────────────────────────────────────────────────────

class StyledButton(ButtonBehavior, BoxLayout):
    """
    A fully Kivy-property-driven rounded button.
    Assigning .bg_color / .press_color / .text_color triggers automatic
    canvas redraws because they are declared as ColorProperty.
    """

    bg_color    = ColorProperty([0.914, 0.271, 0.376, 1])  # ACCENT default
    press_color = ColorProperty([0.780, 0.212, 0.322, 1])  # ACCENT_H default
    text_color  = ColorProperty([1, 1, 1, 1])
    btn_text    = StringProperty("")
    font_size   = NumericProperty(14)

    def __init__(self, btn_text="", bg_color=None, press_color=None,
                 text_color=None, font_size=None, **kwargs):
        super().__init__(**kwargs)
        if bg_color    is not None:
            self.bg_color    = bg_color
        if press_color is not None:
            self.press_color = press_color
        if text_color  is not None:
            self.text_color  = text_color
        if font_size   is not None:
            self.font_size   = font_size
        self.btn_text = btn_text


class DividerLine(Widget):
    pass


class InfoPopup(Popup):
    """Simple modal popup for success / error messages, with optional Retry action."""

    def __init__(self, title="Info", message="", btn_text="OK",
                 btn_color=None, on_dismiss_cb=None, retry_cb=None, **kwargs):
        super().__init__(**kwargs)
        self.title           = title
        self.size_hint       = (0.88, None)
        self.height          = dp(230) if retry_cb else dp(210)
        self.separator_color = ACCENT
        self.background      = ""
        self.background_color = SURFACE

        content = BoxLayout(
            orientation="vertical", padding=dp(16), spacing=dp(12)
        )

        msg_lbl = Label(
            text=message,
            color=TEXT,
            font_size=dp(14),
            halign="center",
            valign="middle",
        )
        msg_lbl.bind(size=msg_lbl.setter("text_size"))
        content.add_widget(msg_lbl)

        btn_row = BoxLayout(
            orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(44)
        )

        if retry_cb:
            dismiss_btn = StyledButton(
                btn_text="DISMISS",
                bg_color=list(SURF2),
                press_color=list(BORDER),
                text_color=list(SUBTEXT),
                font_size=dp(12),
            )
            dismiss_btn.bind(on_release=lambda *_: self.dismiss())
            btn_row.add_widget(dismiss_btn)

            retry_btn = StyledButton(
                btn_text="  RETRY DOWNLOAD",
                bg_color=btn_color or list(ACCENT),
                press_color=list(ACCENT_H),
                text_color=[1, 1, 1, 1],
                font_size=dp(12),
            )
            def _do_retry(*_):
                self.dismiss()
                retry_cb()
            retry_btn.bind(on_release=_do_retry)
            btn_row.add_widget(retry_btn)
        else:
            ok_btn = StyledButton(
                btn_text=btn_text,
                bg_color=btn_color or list(ACCENT),
                press_color=list(ACCENT_H),
                size_hint_y=None,
                height=dp(44),
            )
            ok_btn.bind(on_release=lambda *_: self.dismiss())
            btn_row.add_widget(ok_btn)

        content.add_widget(btn_row)
        self.content = content
        if on_dismiss_cb:
            self.bind(on_dismiss=lambda *_: on_dismiss_cb())


# ── Main screen ───────────────────────────────────────────────────────────────

class DownloaderScreen(BoxLayout):
    """Root widget — entire application UI lives here."""

    is_downloading = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self._cancel_requested = False
        self._type             = "video"
        self._resolution       = "720p"
        self._audio_format     = "mp3"
        self._audio_quality    = "192 kbps"
        self._save_path        = "."

        self._build()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _lbl(self, text, font_size=None, color=None, bold=False,
             halign="left", height=None):
        l = Label(
            text=text,
            font_size=font_size or dp(12),
            color=color or SUBTEXT,
            bold=bold,
            halign=halign,
            valign="middle",
            size_hint_y=None,
            height=height or dp(22),
        )
        l.bind(size=l.setter("text_size"))
        return l

    def _section_label(self, text):
        return self._lbl(text, font_size=dp(11), color=SUBTEXT, bold=True)

    def _input(self, hint=""):
        return TextInput(
            hint_text=hint,
            multiline=False,
            font_size=dp(14),
            background_color=SURF2,
            foreground_color=TEXT,
            hint_text_color=SUBTEXT,
            cursor_color=list(ACCENT),
            size_hint_y=None,
            height=dp(44),
            padding=[dp(12), dp(12), dp(12), dp(12)],
        )

    def _small_btn(self, text, callback):
        btn = StyledButton(
            btn_text=text,
            bg_color=list(SURF2),
            press_color=list(ACCENT),
            text_color=list(SUBTEXT),
            font_size=dp(11),
            size_hint=(None, None),
            size=(dp(80), dp(44)),
        )
        btn.bind(on_release=lambda *_: callback())
        return btn

    def _spinner(self, values, default, callback):
        sp = Spinner(
            text=default,
            values=values,
            font_size=dp(13),
            background_color=SURF2,
            color=TEXT,
            size_hint_y=None,
            height=dp(44),
        )
        sp.bind(text=lambda _inst, val: callback(val))
        return sp

    @staticmethod
    def _gap(h=None):
        return Widget(size_hint_y=None, height=h or dp(14))

    # ── Canvas bg ─────────────────────────────────────────────────────────────

    def _build(self):
        with self.canvas.before:
            Color(*BG)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._upd_bg, size=self._upd_bg)
        self._build_header()
        self._build_scroll_body()
        self._build_footer()

    def _upd_bg(self, *_):
        self._bg_rect.pos  = self.pos
        self._bg_rect.size = self.size

    # ── Header ────────────────────────────────────────────────────────────────

    def _build_header(self):
        hdr = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(64),
            padding=[dp(20), dp(10)],
            spacing=dp(10),
        )
        with hdr.canvas.before:
            Color(*ACCENT)
            self._hdr_rect = Rectangle(pos=hdr.pos, size=hdr.size)
        hdr.bind(
            pos =lambda *_: setattr(self._hdr_rect, "pos",  hdr.pos),
            size=lambda *_: setattr(self._hdr_rect, "size", hdr.size),
        )

        hdr.add_widget(Label(
            text="▶", font_size=dp(26), color=(1, 1, 1, 1),
            bold=True, size_hint=(None, 1), width=dp(36),
        ))

        title_col = BoxLayout(orientation="vertical", spacing=0)
        title_lbl = Label(
            text=APP_NAME, font_size=dp(18), color=(1, 1, 1, 1),
            bold=True, halign="left",
        )
        title_lbl.bind(size=title_lbl.setter("text_size"))
        title_col.add_widget(title_lbl)
        sub_lbl = Label(
            text="Fast  •  Simple  •  Reliable",
            font_size=dp(10),
            color=get_color_from_hex("#f8a5b3"),
            halign="left",
        )
        sub_lbl.bind(size=sub_lbl.setter("text_size"))
        title_col.add_widget(sub_lbl)
        hdr.add_widget(title_col)

        ver_lbl = Label(
            text=APP_VERSION, font_size=dp(10), color=(1, 1, 1, 0.7),
            size_hint=(None, 1), width=dp(60), halign="right", bold=True,
        )
        hdr.add_widget(ver_lbl)
        self.add_widget(hdr)

    # ── Scrollable body ───────────────────────────────────────────────────────

    def _build_scroll_body(self):
        sv   = ScrollView(do_scroll_x=False, size_hint=(1, 1))
        body = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=0,
            padding=[dp(20), dp(18), dp(20), dp(14)],
        )
        body.bind(minimum_height=body.setter("height"))

        # ── URL ───────────────────────────────────────────────────────────────
        body.add_widget(self._section_label("VIDEO URL"))
        body.add_widget(self._gap(dp(6)))

        url_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        self._url_input = self._input(hint="Paste YouTube URL here…")
        url_row.add_widget(self._url_input)
        url_row.add_widget(self._small_btn("PASTE", self._paste_url))
        body.add_widget(url_row)

        body.add_widget(self._gap(dp(18)))

        # ── Type selector ─────────────────────────────────────────────────────
        body.add_widget(self._section_label("DOWNLOAD TYPE"))
        body.add_widget(self._gap(dp(6)))

        seg_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(6))

        self._btn_video = StyledButton(
            btn_text="  Video (MP4)",
            bg_color=list(ACCENT), press_color=list(ACCENT_H),
            text_color=[1, 1, 1, 1], font_size=dp(13),
        )
        self._btn_video.bind(on_release=lambda *_: self._select_type("video"))

        self._btn_audio = StyledButton(
            btn_text="  Audio (M4A)",
            bg_color=list(SURF2), press_color=list(BORDER),
            text_color=list(SUBTEXT), font_size=dp(13),
        )
        self._btn_audio.bind(on_release=lambda *_: self._select_type("audio"))

        seg_row.add_widget(self._btn_video)
        seg_row.add_widget(self._btn_audio)
        body.add_widget(seg_row)

        body.add_widget(self._gap(dp(18)))

        # ── Options ───────────────────────────────────────────────────────────
        body.add_widget(self._section_label("OPTIONS"))
        body.add_widget(self._gap(dp(6)))

        self._video_opts = BoxLayout(
            size_hint_y=None, height=dp(44), spacing=dp(10)
        )
        self._video_opts.add_widget(
            self._lbl("Resolution", font_size=dp(13), color=SUBTEXT)
        )
        self._res_spinner = self._spinner(
            VIDEO_RESOLUTIONS, "720p", self._on_resolution
        )
        self._video_opts.add_widget(self._res_spinner)
        body.add_widget(self._video_opts)

        self._audio_opts = BoxLayout(
            size_hint_y=None, height=dp(44), spacing=dp(6)
        )
        self._audio_opts.add_widget(
            self._lbl("Format", font_size=dp(13), color=SUBTEXT)
        )
        self._afmt_spinner = self._spinner(
            AUDIO_FORMATS, "mp3", self._on_audio_format
        )
        self._audio_opts.add_widget(self._afmt_spinner)

        self._audio_opts.add_widget(
            self._lbl("Quality", font_size=dp(13), color=SUBTEXT)
        )
        self._qual_spinner = self._spinner(
            AUDIO_QUALITIES, "192 kbps", self._on_audio_quality
        )
        self._audio_opts.add_widget(self._qual_spinner)
        self._audio_opts.opacity  = 0
        self._audio_opts.disabled = True
        body.add_widget(self._audio_opts)

        body.add_widget(self._gap(dp(14)))
        body.add_widget(DividerLine())
        body.add_widget(self._gap(dp(12)))

        # ── Save path ─────────────────────────────────────────────────────────
        body.add_widget(self._section_label("SAVE TO"))
        body.add_widget(self._gap(dp(6)))

        self._save_lbl = self._lbl(
            "(setting up…)", font_size=dp(12), color=SUBTEXT, height=dp(36)
        )
        body.add_widget(self._save_lbl)

        body.add_widget(self._gap(dp(18)))

        # ── Action buttons ────────────────────────────────────────────────────
        action_row = BoxLayout(
            size_hint_y=None, height=dp(50), spacing=dp(8)
        )

        self._dl_btn = StyledButton(
            btn_text="  DOWNLOAD",
            bg_color=list(ACCENT), press_color=list(ACCENT_H),
            text_color=[1, 1, 1, 1], font_size=dp(14),
        )
        self._dl_btn.bind(on_release=lambda *_: self._start_download())

        self._cancel_btn = StyledButton(
            btn_text="  CANCEL",
            bg_color=list(SURF2), press_color=list(BORDER),
            text_color=list(SUBTEXT), font_size=dp(13),
            size_hint=(None, 1), width=dp(110),
        )
        self._cancel_btn.disabled = True
        self._cancel_btn.opacity  = 0.4
        self._cancel_btn.bind(on_release=lambda *_: self._cancel_download())

        action_row.add_widget(self._dl_btn)
        action_row.add_widget(self._cancel_btn)
        body.add_widget(action_row)

        body.add_widget(self._gap(dp(14)))

        # ── Progress bar ──────────────────────────────────────────────────────
        self._progress = ProgressBar(
            max=100, value=0, size_hint_y=None, height=dp(10),
        )
        body.add_widget(self._progress)

        body.add_widget(self._gap(dp(8)))

        # ── Info / status labels ──────────────────────────────────────────────
        self._info_lbl = self._lbl(
            "", font_size=dp(12), color=ACCENT, bold=True, height=dp(20)
        )
        body.add_widget(self._info_lbl)

        body.add_widget(self._gap(dp(4)))

        self._status_lbl = self._lbl(
            "Ready", font_size=dp(12), color=SUBTEXT, height=dp(20)
        )
        body.add_widget(self._status_lbl)
        sv.add_widget(body)
        self.add_widget(sv)

    # ── Footer ────────────────────────────────────────────────────────────────

    def _build_footer(self):
        foot = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(52))

        accent_line = Widget(size_hint_y=None, height=dp(2))
        with accent_line.canvas.before:
            Color(*ACCENT)
            self._al_rect = Rectangle(
                pos=accent_line.pos, size=accent_line.size
            )
        accent_line.bind(
            pos =lambda *_: setattr(self._al_rect, "pos",  accent_line.pos),
            size=lambda *_: setattr(self._al_rect, "size", accent_line.size),
        )
        foot.add_widget(accent_line)

        content = BoxLayout(
            orientation="horizontal", padding=[dp(16), dp(6)],
        )
        with foot.canvas.before:
            Color(*SURF2)
            self._ft_rect = Rectangle(pos=foot.pos, size=foot.size)
        foot.bind(
            pos =lambda *_: setattr(self._ft_rect, "pos",  foot.pos),
            size=lambda *_: setattr(self._ft_rect, "size", foot.size),
        )

        foot_lbl = Label(
            text=(
                f"[b][color=e6edf3]{DEV_NAME}[/color][/b]"
                f"[color=484f58]  ·  [/color]"
                f"[color=8b949e]{DEV_ROLE}[/color]"
                f"[color=484f58]  ·  [/color]"
                f"[color=8b949e]{APP_VERSION}[/color]"
            ),
            markup=True,
            font_size=dp(10),
            halign="center",
            valign="middle",
        )
        foot_lbl.bind(size=foot_lbl.setter("text_size"))
        content.add_widget(foot_lbl)
        foot.add_widget(content)
        self.add_widget(foot)

    # ── Interaction ───────────────────────────────────────────────────────────

    def _paste_url(self):
        text = Clipboard.paste()
        if text:
            self._url_input.text = text

    def _select_type(self, val: str):
        self._type = val
        if val == "video":
            self._btn_video.bg_color    = list(ACCENT)
            self._btn_video.press_color = list(ACCENT_H)
            self._btn_video.text_color  = [1, 1, 1, 1]
            self._btn_audio.bg_color    = list(SURF2)
            self._btn_audio.press_color = list(BORDER)
            self._btn_audio.text_color  = list(SUBTEXT)
            self._video_opts.opacity    = 1
            self._video_opts.disabled   = False
            self._audio_opts.opacity    = 0
            self._audio_opts.disabled   = True
        else:
            self._btn_audio.bg_color    = list(ACCENT)
            self._btn_audio.press_color = list(ACCENT_H)
            self._btn_audio.text_color  = [1, 1, 1, 1]
            self._btn_video.bg_color    = list(SURF2)
            self._btn_video.press_color = list(BORDER)
            self._btn_video.text_color  = list(SUBTEXT)
            self._audio_opts.opacity    = 1
            self._audio_opts.disabled   = False
            self._video_opts.opacity    = 0
            self._video_opts.disabled   = True

    def _on_resolution(self, val: str):
        self._resolution = val

    def _on_audio_format(self, val: str):
        self._audio_format = val

    def _on_audio_quality(self, val: str):
        self._audio_quality = val

    # ── Save path ─────────────────────────────────────────────────────────────

    def set_save_path(self, path: str):
        self._save_path      = path
        self._save_lbl.text  = path

    # ── Download flow ─────────────────────────────────────────────────────────

    def _start_download(self):
        url = self._url_input.text.strip()
        if not url:
            self._show_popup(
                "No URL", "Please enter a YouTube URL.", btn_color=list(ACCENT)
            )
            return

        self._cancel_requested    = False
        self._dl_btn.disabled     = True
        self._dl_btn.opacity      = 0.5
        self._cancel_btn.disabled = False
        self._cancel_btn.opacity  = 1.0
        self._progress.value      = 0
        self._info_lbl.text       = ""
        self._set_status("Starting…")

        threading.Thread(target=self._worker, args=(url,), daemon=True).start()

    def _cancel_download(self):
        self._cancel_requested    = True
        self._cancel_btn.disabled = True
        self._cancel_btn.opacity  = 0.4
        self._set_status("Cancelling…")

    def _worker(self, url: str):
        max_attempts = 5
        last_error = None
        current_attempt = 1

        def hook(d):
            if self._cancel_requested:
                raise DownloadCancelled("Cancelled by user.")

            if d["status"] == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                done  = d.get("downloaded_bytes", 0)

                raw_speed = d.get("_speed_str")
                speed = raw_speed.strip() if isinstance(raw_speed, str) else ""

                raw_eta = d.get("_eta_str")
                eta = raw_eta.strip() if isinstance(raw_eta, str) else ""

                size_str = (
                    f"{fmt_bytes(done)} / {fmt_bytes(total)}"
                    if total else fmt_bytes(done)
                )
                parts = [size_str]
                if speed:
                    parts.append(speed)
                if eta:
                    parts.append(f"ETA {eta}")

                if total:
                    pct = done / total * 100
                    Clock.schedule_once(
                        lambda dt, v=pct: self._set_progress(v), 0
                    )
                    Clock.schedule_once(
                        lambda dt, p=pct, att=current_attempt: self._set_status(
                            f"Downloading…  {p:.1f}%" if att == 1 else f"Downloading (Attempt {att}/5)…  {p:.1f}%"
                        ),
                        0,
                    )
                else:
                    Clock.schedule_once(
                        lambda dt, att=current_attempt: self._set_status(
                            "Downloading…" if att == 1 else f"Downloading (Attempt {att}/5)…"
                        ), 0
                    )
                info = "   •   ".join(parts)
                Clock.schedule_once(lambda dt, i=info: self._set_info(i), 0)

            elif d["status"] == "finished":
                Clock.schedule_once(lambda dt: self._set_progress(100), 0)
                Clock.schedule_once(
                    lambda dt: self._set_status("Finalising…"), 0
                )
                Clock.schedule_once(lambda dt: self._set_info(""), 0)

        for attempt in range(1, max_attempts + 1):
            if self._cancel_requested:
                Clock.schedule_once(lambda dt: self._on_cancelled(), 0)
                return

            nonlocal_attempt = attempt
            current_attempt = attempt
            if attempt > 1:
                Clock.schedule_once(
                    lambda dt, a=attempt: self._set_status(
                        f"Retrying download (Attempt {a}/{max_attempts})…"
                    ),
                    0,
                )
                time.sleep(2)

            try:
                download_media(
                    url=url,
                    media_type=self._type,
                    output_path=self._save_path,
                    resolution=self._resolution,
                    audio_format=self._audio_format,
                    audio_quality=self._audio_quality,
                    progress_hook=hook,
                )
                if self._cancel_requested:
                    Clock.schedule_once(lambda dt: self._on_cancelled(), 0)
                else:
                    Clock.schedule_once(lambda dt: self._on_success(), 0)
                return
            except DownloadCancelled:
                Clock.schedule_once(lambda dt: self._on_cancelled(), 0)
                return
            except Exception as exc:
                last_error = exc

        if last_error:
            err = str(last_error)
            Clock.schedule_once(lambda dt, e=err: self._on_error(e), 0)

    # ── UI state (main-thread only) ───────────────────────────────────────────

    def _set_status(self, text: str):
        self._status_lbl.text = text

    def _set_info(self, text: str):
        self._info_lbl.text = text

    def _set_progress(self, val: float):
        self._progress.value = val

    def _reset_buttons(self):
        self._dl_btn.disabled     = False
        self._dl_btn.opacity      = 1.0
        self._cancel_btn.disabled = True
        self._cancel_btn.opacity  = 0.4

    def _on_success(self):
        self._reset_buttons()
        self._set_status("  Download complete!")
        self._set_progress(100)
        self._set_info("")
        self._show_popup(
            "Download Complete",
            "Your file has been saved.\n"
            "Open the Files app  On My iPhone  YT Downloader.",
            btn_text="Great!",
            btn_color=list(SUCCESS),
        )

    def _on_cancelled(self):
        self._reset_buttons()
        self._set_status("  Download cancelled")
        self._set_info("")

    def _on_error(self, msg: str):
        self._reset_buttons()
        self._set_status("  Download error")
        self._set_info("")

        clean_msg = str(msg)
        if "AttributeError" in clean_msg or "'str'" in clean_msg or "'NoneType'" in clean_msg:
            user_msg = "A download parameter error occurred.\nPlease tap Retry Download to try again."
        elif "HTTP Error 429" in clean_msg:
            user_msg = "YouTube rate limit reached.\nPlease wait a moment and tap Retry Download."
        elif "HTTP Error 403" in clean_msg or "Private video" in clean_msg:
            user_msg = "This video is restricted or unavailable.\nPlease check the URL and try again."
        else:
            user_msg = f"{clean_msg[:160]}\nTap Retry Download to try again."

        self._show_popup(
            "Download Failed",
            user_msg,
            btn_color=list(ACCENT),
            retry_cb=self._start_download,
        )

    def _show_popup(self, title: str, message: str,
                    btn_text: str = "OK", btn_color=None, retry_cb=None):
        InfoPopup(
            title=title,
            message=message,
            btn_text=btn_text,
            btn_color=btn_color or list(ACCENT),
            retry_cb=retry_cb,
        ).open()


# ── Application entry point ───────────────────────────────────────────────────

class YTDownloaderApp(App):
    title = APP_NAME

    def build(self):
        # Load KV rules here so dp() is already resolved by the Kivy event loop
        Builder.load_string(KV)
        Window.clearcolor = BG
        self._screen = DownloaderScreen()
        return self._screen

    def on_start(self):
        save_path = self.user_data_dir
        os.makedirs(save_path, exist_ok=True)
        self._screen.set_save_path(save_path)


if __name__ == "__main__":
    YTDownloaderApp().run()
