"""
kv_layout.py — KV language rules for custom widgets.

Loaded by YTDownloaderApp.build() after the Kivy event loop starts so that
dp() is already resolved. Kept separate from screen.py so the layout DSL
can be edited without touching Python logic.
"""

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
