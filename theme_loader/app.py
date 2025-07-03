#!/usr/bin/env python3
"""
GNOME Theme Loader – prototipo
• Arrastra un .zip/.tar.* con un tema o iconos
• Detecta tipo y lo instala en ~/.themes o ~/.icons
"""
from __future__ import annotations
import gi
gi.require_version("Adw", "1")
from gi.repository import Adw
from .ui import Window

class App(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.example.ThemeLoader")
        self.connect("activate", self.on_activate)
        Adw.init()

    def on_activate(self, *_):
        Window(self).present()

def main() -> None:
    import sys
    sys.exit(App().run(sys.argv))

if __name__ == "__main__":
    main()
