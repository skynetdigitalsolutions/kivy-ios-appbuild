import io
import os
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
import urllib.request
import webbrowser
import zipfile
from tkinter import filedialog, messagebox, ttk

import yt_dlp
from yt_dlp.utils import DownloadCancelled

try:
    import pyttsx3

    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

FFMPEG_LOCATION = None

# ── Options exposed to the UI ─────────────────────────────────────────────────
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


def _get_ffmpeg_location():
    """Get or install FFmpeg location for Windows."""
    global FFMPEG_LOCATION

    if FFMPEG_LOCATION and os.path.exists(os.path.join(FFMPEG_LOCATION, "ffmpeg.exe")):
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

    try:
        ffmpeg_base = os.path.join(os.path.dirname(sys.executable), "ffmpeg")
        os.makedirs(ffmpeg_base, exist_ok=True)

        ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"

        temp_zip = os.path.join(tempfile.gettempdir(), "ffmpeg.zip")
        urllib.request.urlretrieve(ffmpeg_url, temp_zip)

        with zipfile.ZipFile(temp_zip, "r") as zip_ref:
            zip_ref.extractall(temp_zip.replace(".zip", ""))

        extracted_dir = temp_zip.replace(".zip", "")
        for item in os.listdir(extracted_dir):
            if "ffmpeg" in item.lower():
                src_bin = os.path.join(extracted_dir, item, "bin")
                dst_bin = os.path.join(ffmpeg_base, "bin")
                if os.path.exists(dst_bin):
                    shutil.rmtree(dst_bin)
                shutil.copytree(src_bin, dst_bin)
                break

        os.remove(temp_zip)
        shutil.rmtree(extracted_dir)

        FFMPEG_LOCATION = os.path.join(ffmpeg_base, "bin")
        return FFMPEG_LOCATION

    except Exception:
        pass

    try:
        subprocess.run(
            [
                "winget",
                "install",
                "--id",
                "Gyan.FFmpeg",
                "-e",
                "--accept-source-agreements",
                "--accept-package-agreements",
            ],
            check=True,
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
        )

        winget_paths = [
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WinGet", "Packages"),
            os.path.join(os.environ.get("PROGRAMFILES", ""), "FFmpeg"),
            os.path.join(os.environ.get("ProgramFiles(x86)", ""), "FFmpeg"),
        ]

        for base_path in winget_paths:
            if os.path.exists(base_path):
                for root, dirs, files in os.walk(base_path):
                    if "ffmpeg.exe" in files and "bin" in root.lower():
                        FFMPEG_LOCATION = root
                        return FFMPEG_LOCATION

        try:
            result = subprocess.run(["where", "ffmpeg"], capture_output=True, text=True, check=True)
            ffmpeg_path = os.path.dirname(result.stdout.strip().split("\n")[0])
            FFMPEG_LOCATION = ffmpeg_path
            return FFMPEG_LOCATION
        except Exception:
            pass

    except Exception:
        pass

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
    """Download video (MP4) or audio from a YouTube URL."""
    ffmpeg_path = _get_ffmpeg_location()
    bitrate = audio_quality.replace(" kbps", "")

    base = {
        "ffmpeg_location": ffmpeg_path,
        "socket_timeout": 30,
        "retries": 10,
        "fragment_retries": 10,
        "retry_sleep_functions": {"http": lambda n: min(4 * n, 30)},
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

    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])


# ── Branding ──────────────────────────────────────────────────────────────────
APP_NAME = "YT Downloader"
APP_VERSION = "v2.0.0"
DEV_NAME = "Tony Bbosa"
DEV_ROLE = "Full-Stack Developer"
DEV_CONTACT = "github.com/tonybbosa"

# ── Ad config — swap these two values to change the ad ───────────────────────
# AD_IMAGE_URL : direct link to your banner image (728x90 or any size)
# AD_CLICK_URL : URL that opens when the user clicks the banner
AD_IMAGE_URL = ""  # e.g. "https://yourcdn.com/banner.png"
AD_CLICK_URL = ""  # e.g. "https://your-sponsor.com"

# ── Colour palette ────────────────────────────────────────────────────────────
BG = "#0d1117"  # root background
SURFACE = "#161b22"  # main content surface
SURF2 = "#21262d"  # inputs / secondary cards
BORDER = "#30363d"  # subtle borders
ACCENT = "#e94560"  # primary red
ACCENT_H = "#c73652"  # accent hover / pressed
TEXT = "#e6edf3"  # primary text
SUBTEXT = "#8b949e"  # labels / hints
MUTED = "#484f58"  # separators / dots
SUCCESS = "#3fb950"  # success green


def fmt_bytes(n: float) -> str:
    if not n:
        return "?"
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.2f} TB"


class YTDownloaderApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("620x660")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        self.url_var = tk.StringVar()
        self.type_var = tk.StringVar(value="video")
        self.res_var = tk.StringVar(value="720p")
        self.afmt_var = tk.StringVar(value="mp3")
        self.aqual_var = tk.StringVar(value="192 kbps")
        self.output_var = tk.StringVar(
            value=os.path.join(os.path.expanduser("~"), "Downloads")
        )
        self.progress_var = tk.DoubleVar()
        self.info_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")

        self._seg_btns: dict[str, tk.Button] = {}
        self._cancel_requested = False
        self._is_downloading = False

        self._speech_q: queue.Queue = queue.Queue()
        self._start_speech_worker()

        self._setup_styles()
        self._build_header()
        self._build_body()
        self._build_ad_banner()
        self._build_footer()

    def _start_speech_worker(self):
        if not TTS_AVAILABLE:
            return

        def _worker():
            try:
                engine = pyttsx3.init()
                engine.setProperty("rate", 170)
                engine.setProperty("volume", 1.0)
                while True:
                    text = self._speech_q.get()
                    if text is None:
                        break
                    engine.say(text)
                    engine.runAndWait()
            except Exception:
                pass

        threading.Thread(target=_worker, daemon=True).start()

    def _speak(self, text: str):
        if TTS_AVAILABLE:
            self._speech_q.put(text)

    def _speak_error(self, msg: str):
        clean = " ".join(str(msg).split())
        if clean:
            self._speak(f"Error. {clean}")

    def _completion_message(self) -> str:
        if self.type_var.get() == "audio":
            return "Audio download complete. Your file has been saved successfully."
        return "Video download complete. Your file has been saved successfully."

    def _setup_styles(self):
        s = ttk.Style()
        s.theme_use("clam")

        s.configure(
            "App.Horizontal.TProgressbar",
            troughcolor=SURF2,
            background=ACCENT,
            bordercolor=SURFACE,
            lightcolor=ACCENT,
            darkcolor=ACCENT,
            thickness=9,
        )

        s.configure(
            "App.TCombobox",
            fieldbackground=SURF2,
            background=SURF2,
            foreground=TEXT,
            arrowcolor=SUBTEXT,
            selectbackground=ACCENT,
            selectforeground=TEXT,
            bordercolor=BORDER,
            padding=(8, 6),
        )
        s.map(
            "App.TCombobox",
            fieldbackground=[("readonly", SURF2)],
            foreground=[("readonly", TEXT)],
            selectbackground=[("readonly", SURF2)],
            selectforeground=[("readonly", TEXT)],
        )

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=ACCENT, height=60)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        left = tk.Frame(hdr, bg=ACCENT)
        left.pack(side="left", padx=22, pady=10)
        tk.Label(
            left, text="▶", font=("Segoe UI", 22, "bold"), bg=ACCENT, fg="white"
        ).pack(side="left", padx=(0, 9))
        title_f = tk.Frame(left, bg=ACCENT)
        title_f.pack(side="left")
        tk.Label(
            title_f, text=APP_NAME, font=("Segoe UI", 15, "bold"), bg=ACCENT, fg="white"
        ).pack(anchor="w")
        tk.Label(
            title_f,
            text="Fast  •  Simple  •  Reliable",
            font=("Segoe UI", 7),
            bg=ACCENT,
            fg="#f8a5b3",
        ).pack(anchor="w")

        badge = tk.Frame(hdr, bg=ACCENT_H, padx=10, pady=4)
        badge.pack(side="right", padx=22, pady=20)
        tk.Label(
            badge,
            text=APP_VERSION,
            font=("Segoe UI", 8, "bold"),
            bg=ACCENT_H,
            fg="white",
        ).pack()

    def _build_body(self):
        body = tk.Frame(self.root, bg=SURFACE)
        body.pack(fill="both", expand=True)

        pad = tk.Frame(body, bg=SURFACE)
        pad.pack(fill="both", expand=True, padx=26, pady=(20, 12))
        pad.columnconfigure(0, weight=1)

        r = 0

        self._sec_label(pad, "VIDEO URL").grid(row=r, column=0, sticky="w", pady=(0, 5))
        r += 1

        url_row = self._row_frame(pad)
        url_row.grid(row=r, column=0, sticky="ew")
        self._entry(url_row, self.url_var).grid(
            row=0, column=0, sticky="ew", ipady=9, padx=(0, 8)
        )
        self._pill_btn(url_row, "PASTE", self._paste_url).grid(row=0, column=1, ipady=9)
        r += 1

        self._sec_label(pad, "DOWNLOAD TYPE").grid(
            row=r, column=0, sticky="w", pady=(16, 6)
        )
        r += 1

        seg_frame = tk.Frame(pad, bg=SURFACE)
        seg_frame.grid(row=r, column=0, sticky="w")
        for icon, label, val in [
            ("🎬", "Video  (MP4)", "video"),
            ("🎵", "Audio Only", "audio"),
        ]:
            btn = tk.Button(
                seg_frame,
                text=f"{icon}   {label}",
                command=lambda v=val: self._select_type(v),
                font=("Segoe UI", 10, "bold"),
                relief="flat",
                cursor="hand2",
                padx=20,
                pady=9,
            )
            btn.pack(side="left", padx=(0, 3))
            self._seg_btns[val] = btn
        self._refresh_seg()
        r += 1

        self._sec_label(pad, "OPTIONS").grid(row=r, column=0, sticky="w", pady=(16, 6))
        r += 1

        self.opt_container = tk.Frame(pad, bg=SURFACE)
        self.opt_container.grid(row=r, column=0, sticky="ew")

        self.video_opts = tk.Frame(self.opt_container, bg=SURFACE)
        self._opt_label(self.video_opts, "Resolution").pack(side="left", padx=(0, 10))
        self._combo(self.video_opts, self.res_var, VIDEO_RESOLUTIONS, 14).pack(
            side="left"
        )

        self.audio_opts = tk.Frame(self.opt_container, bg=SURFACE)
        self._opt_label(self.audio_opts, "Format").pack(side="left", padx=(0, 8))
        self._combo(self.audio_opts, self.afmt_var, AUDIO_FORMATS, 7).pack(
            side="left", padx=(0, 22)
        )
        self._opt_label(self.audio_opts, "Quality").pack(side="left", padx=(0, 8))
        self._combo(self.audio_opts, self.aqual_var, AUDIO_QUALITIES, 11).pack(
            side="left"
        )

        self.video_opts.pack(fill="x")
        r += 1

        tk.Frame(pad, bg=BORDER, height=1).grid(
            row=r, column=0, sticky="ew", pady=(16, 0)
        )
        r += 1

        self._sec_label(pad, "SAVE TO").grid(row=r, column=0, sticky="w", pady=(12, 5))
        r += 1

        save_row = self._row_frame(pad)
        save_row.grid(row=r, column=0, sticky="ew")
        self._entry(save_row, self.output_var, readonly=True).grid(
            row=0, column=0, sticky="ew", ipady=9, padx=(0, 8)
        )
        self._pill_btn(save_row, "BROWSE", self._browse).grid(row=0, column=1, ipady=9)
        r += 1

        action_row = self._row_frame(pad)
        action_row.grid(row=r, column=0, sticky="ew", pady=(18, 0))
        action_row.columnconfigure(0, weight=1)

        self.dl_btn = tk.Button(
            action_row,
            text="⬇   DOWNLOAD",
            command=self._start_download,
            font=("Segoe UI", 12, "bold"),
            bg=ACCENT,
            fg="white",
            activebackground=ACCENT_H,
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            pady=12,
        )
        self.dl_btn.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.dl_btn.bind("<Enter>", lambda _: self.dl_btn.config(bg=ACCENT_H))
        self.dl_btn.bind("<Leave>", lambda _: self.dl_btn.config(bg=ACCENT))

        self.cancel_btn = tk.Button(
            action_row,
            text="✖   CANCEL",
            command=self._cancel_download,
            font=("Segoe UI", 12, "bold"),
            bg=SURF2,
            fg=TEXT,
            activebackground=BORDER,
            activeforeground=TEXT,
            relief="flat",
            cursor="hand2",
            pady=12,
            state="disabled",
            padx=18,
        )
        self.cancel_btn.grid(row=0, column=1, sticky="ew")
        r += 1

        self.pb = ttk.Progressbar(
            pad,
            variable=self.progress_var,
            maximum=100,
            style="App.Horizontal.TProgressbar",
        )
        self.pb.grid(row=r, column=0, sticky="ew", pady=(14, 4))
        r += 1

        tk.Label(
            pad,
            textvariable=self.info_var,
            font=("Segoe UI", 9, "bold"),
            bg=SURFACE,
            fg=ACCENT,
        ).grid(row=r, column=0, sticky="w")
        r += 1

        tk.Label(
            pad,
            textvariable=self.status_var,
            font=("Segoe UI", 9),
            bg=SURFACE,
            fg=SUBTEXT,
        ).grid(row=r, column=0, sticky="w", pady=(2, 0))

    def _build_ad_banner(self):
        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x")

        self._ad_frame = tk.Frame(self.root, bg=SURF2, height=80, cursor="hand2")
        self._ad_frame.pack(fill="x")
        self._ad_frame.pack_propagate(False)

        tk.Label(
            self._ad_frame,
            text="AD",
            font=("Segoe UI", 7, "bold"),
            bg=MUTED,
            fg=SUBTEXT,
            padx=4,
            pady=1,
        ).place(relx=1.0, x=-6, y=4, anchor="ne")

        self._ad_label = tk.Label(
            self._ad_frame,
            text="📊  Advertise here  —  contact: tonybbosa@gmail.com",
            font=("Segoe UI", 9),
            bg=SURF2,
            fg=MUTED,
            cursor="hand2",
        )
        self._ad_label.place(relx=0.5, rely=0.5, anchor="center")
        self._ad_label.bind("<Button-1>", self._ad_clicked)
        self._ad_frame.bind("<Button-1>", self._ad_clicked)

        if AD_IMAGE_URL:
            threading.Thread(target=self._fetch_ad_image, daemon=True).start()

    def _fetch_ad_image(self):
        try:
            from PIL import Image, ImageTk

            req = urllib.request.Request(
                AD_IMAGE_URL,
                headers={"User-Agent": "YTDownloader-AdClient/1.0"},
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = resp.read()

            img = Image.open(io.BytesIO(data)).convert("RGBA")
            bw = 620
            ratio = bw / img.width
            bh = min(int(img.height * ratio), 80)
            img = img.resize((bw, bh), Image.LANCZOS)

            photo = ImageTk.PhotoImage(img)
            self.root.after(0, self._show_ad_image, photo)
        except Exception:
            pass

    def _show_ad_image(self, photo):
        self._ad_photo_ref = photo
        self._ad_label.config(image=photo, text="", bg=SURF2)
        self._ad_label.place(relx=0, rely=0, anchor="nw", width=620, height=80)

    def _ad_clicked(self, _event=None):
        if AD_CLICK_URL:
            webbrowser.open(AD_CLICK_URL)

    def _build_footer(self):
        foot = tk.Frame(self.root, bg=SURF2, height=44)
        foot.pack(fill="x", side="bottom")
        foot.pack_propagate(False)

        tk.Frame(foot, bg=ACCENT, height=2).pack(fill="x", side="top")

        content = tk.Frame(foot, bg=SURF2)
        content.pack(expand=True)

        def _ft(text, bold=False, color=SUBTEXT):
            tk.Label(
                content,
                text=text,
                font=("Segoe UI", 9, "bold" if bold else "normal"),
                bg=SURF2,
                fg=color,
            ).pack(side="left")

        _ft(DEV_NAME, bold=True, color=TEXT)
        _ft("   ·   ", color=MUTED)
        _ft(DEV_ROLE)
        _ft("   ·   ", color=MUTED)
        _ft(DEV_CONTACT, color=SUBTEXT)
        _ft("   ·   ", color=MUTED)
        _ft(APP_VERSION, color=MUTED)

    def _sec_label(self, parent, text: str):
        return tk.Label(
            parent,
            text=text,
            font=("Segoe UI", 8, "bold"),
            bg=SURFACE,
            fg=SUBTEXT,
            anchor="w",
        )

    def _opt_label(self, parent, text: str):
        return tk.Label(parent, text=text, font=("Segoe UI", 9), bg=SURFACE, fg=SUBTEXT)

    def _row_frame(self, parent):
        f = tk.Frame(parent, bg=SURFACE)
        f.columnconfigure(0, weight=1)
        return f

    def _entry(self, parent, var, readonly=False):
        return tk.Entry(
            parent,
            textvariable=var,
            state="readonly" if readonly else "normal",
            font=("Segoe UI", 10),
            bg=SURF2,
            fg=TEXT,
            insertbackground=TEXT,
            readonlybackground=SURF2,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=ACCENT,
        )

    def _pill_btn(self, parent, text: str, cmd):
        return tk.Button(
            parent,
            text=text,
            command=cmd,
            font=("Segoe UI", 8, "bold"),
            bg=SURF2,
            fg=SUBTEXT,
            activebackground=ACCENT,
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=14,
        )

    def _combo(self, parent, var, values, width: int):
        return ttk.Combobox(
            parent,
            textvariable=var,
            values=values,
            state="readonly",
            width=width,
            style="App.TCombobox",
        )

    def _select_type(self, val: str):
        self.type_var.set(val)
        self._refresh_seg()
        self._swap_opts()

    def _refresh_seg(self):
        active = self.type_var.get()
        for val, btn in self._seg_btns.items():
            if val == active:
                btn.config(
                    bg=ACCENT,
                    fg="white",
                    activebackground=ACCENT_H,
                    activeforeground="white",
                )
            else:
                btn.config(
                    bg=SURF2, fg=SUBTEXT, activebackground=BORDER, activeforeground=TEXT
                )

    def _swap_opts(self):
        if self.type_var.get() == "video":
            self.audio_opts.pack_forget()
            self.video_opts.pack(fill="x")
        else:
            self.video_opts.pack_forget()
            self.audio_opts.pack(fill="x")

    def _paste_url(self):
        try:
            self.url_var.set(self.root.clipboard_get())
        except tk.TclError:
            pass

    def _browse(self):
        folder = filedialog.askdirectory(initialdir=self.output_var.get())
        if folder:
            self.output_var.set(folder)

    def _start_download(self):
        url = self.url_var.get().strip()
        if not url:
            msg = "Please enter a YouTube URL."
            self._speak_error(msg)
            messagebox.showwarning("No URL", msg)
            return
        self._cancel_requested = False
        self._is_downloading = True
        self.dl_btn.config(state="disabled")
        self.cancel_btn.config(state="normal")
        self.progress_var.set(0)
        self.info_var.set("")
        self.status_var.set("Starting…")
        threading.Thread(target=self._worker, args=(url,), daemon=True).start()

    def _cancel_download(self):
        if not self._is_downloading:
            return
        self._cancel_requested = True
        self.cancel_btn.config(state="disabled")
        self.status_var.set("Cancelling…")

    def _worker(self, url: str):
        def hook(d):
            if self._cancel_requested:
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
                    self.root.after(0, self.progress_var.set, pct)
                    self.root.after(0, self.status_var.set, f"Downloading…  {pct:.1f}%")
                else:
                    self.root.after(0, self.status_var.set, "Downloading…")
                self.root.after(0, self.info_var.set, "   •   ".join(parts))

            elif d["status"] == "finished":
                self.root.after(0, self.progress_var.set, 100)
                self.root.after(0, self.status_var.set, "Finalising…")
                self.root.after(0, self.info_var.set, "")

        try:
            download_media(
                url=url,
                media_type=self.type_var.get(),
                output_path=self.output_var.get(),
                resolution=self.res_var.get(),
                audio_format=self.afmt_var.get(),
                audio_quality=self.aqual_var.get(),
                progress_hook=hook,
            )
            if self._cancel_requested:
                self.root.after(0, self._on_cancelled)
            else:
                self.root.after(0, self._on_success)
        except DownloadCancelled:
            self.root.after(0, self._on_cancelled)
        except Exception as exc:
            self.root.after(0, self._on_error, str(exc))

    def _on_success(self):
        self._is_downloading = False
        self._cancel_requested = False
        self.status_var.set("✔   Download complete!")
        self.progress_var.set(100)
        self.dl_btn.config(state="normal")
        self.cancel_btn.config(state="disabled")
        spoken_message = self._completion_message()
        self._speak(spoken_message)
        messagebox.showinfo("Done", "Your file has been saved successfully.")

    def _on_cancelled(self):
        self._is_downloading = False
        self._cancel_requested = False
        self.status_var.set("✖   Download cancelled")
        self.info_var.set("")
        self.dl_btn.config(state="normal")
        self.cancel_btn.config(state="disabled")
        self._speak("Download cancelled.")

    def _on_error(self, msg: str):
        self._is_downloading = False
        self._cancel_requested = False
        self.status_var.set(f"✖   {msg[:90]}")
        self.info_var.set("")
        self.dl_btn.config(state="normal")
        self.cancel_btn.config(state="disabled")
        self._speak_error(msg)
        messagebox.showerror("Download Failed", msg)


if __name__ == "__main__":
    root = tk.Tk()

    try:
        base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        png_path = os.path.join(base, "icon.png")
        ico_path = os.path.join(base, "convertico-yt (1).ico")
        if os.path.exists(png_path):
            _icon = tk.PhotoImage(file=png_path)
            root.iconphoto(True, _icon)
        elif os.path.exists(ico_path):
            root.iconbitmap(ico_path)
    except Exception:
        pass

    YTDownloaderApp(root)
    root.mainloop()
