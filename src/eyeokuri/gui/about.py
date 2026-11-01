"""The About window: version, license, and the third-party notices."""

from __future__ import annotations

import sys
import tkinter as tk
import webbrowser
from importlib import resources
from pathlib import Path
from tkinter import ttk
from typing import TYPE_CHECKING

from eyeokuri import __version__
from eyeokuri.gui.model import find_notice_file
from eyeokuri.gui.tkutil import place_over
from eyeokuri.i18n import _

if TYPE_CHECKING:
    from eyeokuri.gui.main_window import MainWindow

REPO = "https://github.com/lulalala/eyeokuri"


def _folders() -> list[Path]:
    """Where the license files sit: next to the executable in the Windows build, in the repository root when run from source."""
    if getattr(sys, "frozen", False):
        return [Path(sys.executable).parent]
    return [Path(__file__).resolve().parents[3]]


class AboutWindow:
    def __init__(self, app: MainWindow) -> None:
        self.app = app
        self.win = tk.Toplevel(app.root)
        self.win.withdraw()
        self.win.title(_("About eyeokuri"))
        self.win.resizable(False, False)
        self.win.transient(app.root)
        self.notice: tk.Toplevel | None = None
        body = ttk.Frame(self.win, padding=16)
        body.pack(fill="both", expand=True)
        icon = resources.files("eyeokuri") / "icons" / "eyeokuri-64.png"
        self.icon = tk.PhotoImage(master=self.win, data=icon.read_bytes())
        ttk.Label(body, image=self.icon).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        ttk.Label(body, text=f"eyeokuri {__version__}", font=("TkDefaultFont", 12, "bold")).grid(row=1, column=0, columnspan=2, sticky="w")
        ttk.Label(
            body,
            text=_("Advance a visual novel with eye and head gestures.") + "\n" + _("Camera frames stay on your PC."),
            justify="left",
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(4, 8))
        ttk.Label(
            body,
            text=_("Licensed under the Apache License 2.0. The face model is Google's MediaPipe Face Landmarker, also Apache 2.0."),
            wraplength=360,
            justify="left",
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 12))
        ttk.Button(body, text=_("License"), command=lambda: self.show_notice("LICENSE", _("License"))).grid(row=4, column=0, sticky="ew", padx=(0, 4))
        ttk.Button(body, text=_("Third-party notices"), command=lambda: self.show_notice("THIRD_PARTY_NOTICES.md", _("Third-party notices"))).grid(row=4, column=1, sticky="ew")
        body.columnconfigure((0, 1), weight=1, uniform="buttons")
        self.win.bind("<Escape>", lambda _e: self.close())
        self.win.protocol("WM_DELETE_WINDOW", self.close)
        place_over(self.win, app.root)

    def show_notice(self, name: str, title: str) -> None:
        """Shows a license file in a window of its own, or opens the repository's copy when the shipped one is missing."""
        if self.notice is not None:
            self.notice.destroy()
        path = find_notice_file(name, _folders())
        if path is None:
            webbrowser.open(f"{REPO}/blob/master/{name}")
            return
        win = tk.Toplevel(self.win)
        self.notice = win
        win.withdraw()
        win.title(title)
        win.transient(self.win)
        frame = ttk.Frame(win, padding=8)
        frame.pack(fill="both", expand=True)
        text = tk.Text(frame, width=88, height=28, wrap="word", font="TkFixedFont", borderwidth=0)
        scroll = ttk.Scrollbar(frame, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        text.insert("1.0", path.read_text(encoding="utf-8"))
        text.configure(state="disabled")
        text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        win.bind("<Escape>", lambda _e: win.destroy())
        place_over(win, self.win)

    def close(self) -> None:
        self.app.about = None
        self.win.destroy()
