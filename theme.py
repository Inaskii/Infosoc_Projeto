"""Shared visual tokens for the VeriUnB application."""

import tkinter as tk

BG = "#F6F9F7"
BLUE = "#003366"
GREEN = "#006633"
LIGHT_GREEN = "#E3F3EA"
TEXT = "#183247"
MUTED = "#637381"
BORDER = "#D6E1E0"
WHITE = "#FFFFFF"
ERROR = "#A32929"
ERROR_BG = "#FCEAEA"
WARNING = "#8A5A00"
WARNING_BG = "#FFF4D6"

FONT_BODY = "Inter"
FONT_DISPLAY = "Montserrat"


def font(size: int, bold: bool = False) -> tuple[str, int, str]:
    return (FONT_DISPLAY if bold else FONT_BODY, size, "bold" if bold else "normal")


def configure_ttk(style: object) -> None:
    """Configure ttk styles without requiring optional font packages."""
    style.configure("App.TFrame", background=BG)
    style.configure("Card.TFrame", background=WHITE)
    style.configure("Sidebar.TFrame", background=BLUE)
    style.configure("Body.TLabel", background=BG, foreground=TEXT, font=font(11))
    style.configure("Muted.TLabel", background=BG, foreground=MUTED, font=font(10))
    style.configure("Card.TLabel", background=WHITE, foreground=TEXT, font=font(11))
    style.configure("Title.TLabel", background=BG, foreground=BLUE, font=font(24, True))
    style.configure("CardTitle.TLabel", background=WHITE, foreground=BLUE, font=font(14, True))
    style.configure("Sidebar.TLabel", background=BLUE, foreground=WHITE, font=font(11))
    style.configure("SidebarMuted.TLabel", background=BLUE, foreground="#B9D2E3", font=font(9))
    style.configure("Primary.TButton", background=BLUE, foreground=WHITE, font=font(11, True), padding=(16, 9))
    style.map("Primary.TButton", background=[("active", "#174D80"), ("disabled", "#7D97AC")])
    style.configure("Secondary.TButton", background=WHITE, foreground=BLUE, font=font(10), padding=(12, 7))
    style.map("Secondary.TButton", background=[("active", LIGHT_GREEN)])
    style.configure("Danger.TButton", background=WHITE, foreground=ERROR, font=font(10), padding=(10, 6))
    style.map("Danger.TButton", background=[("active", ERROR_BG)])
