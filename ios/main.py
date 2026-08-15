"""
main.py — YT Downloader iOS App entry point.
Authors: Mpagi William & Tony Bbosa (skynetdigitalsolutionsug@gmail.com)

This file is intentionally minimal: Kivy app initialisation only.
All application logic lives in the app/ package:
  app/constants.py  — colours, metadata, format maps
  app/downloader.py — FFmpeg discovery, yt-dlp download logic
  app/kv_layout.py  — KV canvas/widget rules
  app/widgets.py    — StyledButton, DividerLine, InfoPopup
  app/screen.py     — DownloaderScreen (UI + interaction + threading)
"""

import os

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder

from app.constants import APP_NAME, BG
from app.kv_layout import KV
from app.screen import DownloaderScreen


class YTDownloaderApp(App):
    title = APP_NAME

    def build(self):
        # Load KV rules here so dp() is already resolved by the Kivy event loop.
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
