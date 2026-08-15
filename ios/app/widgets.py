"""
widgets.py — Reusable Kivy widgets: StyledButton, DividerLine, InfoPopup.
Extracted verbatim from original main.py. Requires kv_layout.KV to be
loaded before widgets are instantiated (handled by YTDownloaderApp.build).
"""

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
from kivy.uix.widget import Widget

from .constants import ACCENT, ACCENT_H, BORDER, SUBTEXT, SURF2, SURFACE, TEXT


# ── StyledButton ──────────────────────────────────────────────────────────────

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


# ── DividerLine ───────────────────────────────────────────────────────────────

class DividerLine(Widget):
    """A thin horizontal rule — styled via KV (see kv_layout.py)."""
    pass


# ── InfoPopup ─────────────────────────────────────────────────────────────────

class InfoPopup(Popup):
    """
    Modal popup for success / error messages with an optional Retry action.

    Parameters
    ----------
    title        : Popup title bar text.
    message      : Body message shown to the user.
    btn_text     : Label for the single OK button (ignored when retry_cb given).
    btn_color    : Background colour for the primary action button.
    on_dismiss_cb: Callable invoked after the popup is dismissed.
    retry_cb     : If provided, renders DISMISS + RETRY DOWNLOAD buttons.
    """

    def __init__(self, title="Info", message="", btn_text="OK",
                 btn_color=None, on_dismiss_cb=None, retry_cb=None, **kwargs):
        super().__init__(**kwargs)
        self.title            = title
        self.size_hint        = (0.88, None)
        self.height           = dp(230) if retry_cb else dp(210)
        self.separator_color  = ACCENT
        self.background       = ""
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
            orientation="horizontal", spacing=dp(8),
            size_hint_y=None, height=dp(44)
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
