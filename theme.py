"""
theme.py  –  DocFlow Manager · Design System
Premium accounting-software aesthetic (Xero / QuickBooks / SAP style)
"""
import tkinter as tk
from tkinter import ttk

# ══════════════════════════════════════════════════════════════════
# COLOUR PALETTE
# ══════════════════════════════════════════════════════════════════
BG_DARKEST   = "#0c1220"   # deepest bar
BG_DARK      = "#111827"   # header
BG_MEDIUM    = "#1e293b"   # user chip / sub-header
BG_PAGE      = "#f1f5f9"   # page background
BG_CARD      = "#ffffff"   # card / panel
BG_ROW_ALT   = "#f8fafc"   # alternate table row
BG_INPUT     = "#f1f5f9"   # entry field
BG_INPUT_FOC = "#eff6ff"   # entry field – focused

BORDER       = "#e2e8f0"
BORDER_FOCUS = "#93c5fd"

TEXT_DARK    = "#0f172a"
TEXT_MED     = "#334155"
TEXT_MUTED   = "#64748b"
TEXT_GHOST   = "#94a3b8"
TEXT_WHITE   = "#ffffff"
TEXT_OFFWHITE= "#e2e8f0"

# Module accent colours
BLUE         = "#2563eb";  BLUE_H   = "#1d4ed8"
GREEN        = "#059669";  GREEN_H  = "#047857"
AMBER        = "#d97706";  AMBER_H  = "#b45309"
PURPLE       = "#7c3aed";  PURPLE_H = "#6d28d9"
RED          = "#dc2626";  RED_H    = "#b91c1c"
CYAN         = "#0891b2";  CYAN_H   = "#0e7490"
INDIGO       = "#4f46e5";  INDIGO_H = "#4338ca"
SLATE        = "#475569";  SLATE_H  = "#334155"

# Status colours
S_SUCCESS_BG = "#dcfce7";  S_SUCCESS_FG = "#15803d"
S_WARN_BG    = "#fef9c3";  S_WARN_FG    = "#a16207"
S_ERROR_BG   = "#fee2e2";  S_ERROR_FG   = "#b91c1c"
S_INFO_BG    = "#dbeafe";  S_INFO_FG    = "#1d4ed8"

# ══════════════════════════════════════════════════════════════════
# TYPOGRAPHY
# ══════════════════════════════════════════════════════════════════
FF = "Segoe UI"

F_DISPLAY = (FF, 22, "bold")
F_H1      = (FF, 16, "bold")
F_H2      = (FF, 13, "bold")
F_H3      = (FF, 11, "bold")
F_BODY    = (FF, 10)
F_BODY_B  = (FF, 10, "bold")
F_SMALL   = (FF, 9)
F_SMALL_B = (FF, 9, "bold")
F_CAPTION = (FF, 8)

# ══════════════════════════════════════════════════════════════════
# DIMENSIONS
# ══════════════════════════════════════════════════════════════════
WIN_W     = 1400
WIN_H     = 900
HDR_H     = 64      # header bar height
STEP_H    = 56      # step-indicator bar height
SIDE_PAD  = 32      # horizontal page padding

# ══════════════════════════════════════════════════════════════════
# TTK STYLE CONFIGURATION  (call once per session)
# ══════════════════════════════════════════════════════════════════
def configure_styles():
    s = ttk.Style()

    # ── Treeview ──────────────────────────────────────────────────
    s.configure("Premium.Treeview",
                font=F_BODY, rowheight=34,
                background=BG_CARD, fieldbackground=BG_CARD,
                foreground=TEXT_DARK, borderwidth=0, relief="flat")
    s.configure("Premium.Treeview.Heading",
                font=F_SMALL_B,
                background=BG_PAGE, foreground=TEXT_MUTED,
                relief="flat", borderwidth=0, padding=(8, 6))
    s.map("Premium.Treeview",
          background=[("selected", INDIGO)],
          foreground=[("selected", TEXT_WHITE)])

    # ── Scrollbar ─────────────────────────────────────────────────
    s.configure("Premium.Vertical.TScrollbar",
                background=BG_PAGE, troughcolor=BORDER,
                borderwidth=0, arrowsize=12, relief="flat")
    s.configure("Premium.Horizontal.TScrollbar",
                background=BG_PAGE, troughcolor=BORDER,
                borderwidth=0, arrowsize=12, relief="flat")

    # ── Combobox ──────────────────────────────────────────────────
    s.configure("Premium.TCombobox",
                font=F_BODY,
                fieldbackground=BG_INPUT, background=BG_CARD,
                foreground=TEXT_DARK, padding=(6, 5),
                relief="flat")
    s.map("Premium.TCombobox",
          fieldbackground=[("readonly", BG_INPUT)],
          foreground=[("readonly", TEXT_DARK)])

    # ── Progressbar ───────────────────────────────────────────────
    s.configure("Premium.Horizontal.TProgressbar",
                troughcolor=BORDER, background=INDIGO,
                thickness=5, relief="flat")

    # ── Notebook (tabs) ───────────────────────────────────────────
    s.configure("Premium.TNotebook",
                background=BG_PAGE, borderwidth=0)
    s.configure("Premium.TNotebook.Tab",
                font=F_BODY, padding=(14, 8),
                background=BORDER, foreground=TEXT_MUTED)
    s.map("Premium.TNotebook.Tab",
          background=[("selected", BG_CARD)],
          foreground=[("selected", TEXT_DARK)])


# ══════════════════════════════════════════════════════════════════
# HEADER FACTORY
# ══════════════════════════════════════════════════════════════════
def build_header(window,
                 title: str,
                 subtitle: str,
                 username: str,
                 accent: str = INDIGO,
                 on_close=None) -> tk.Frame:
    """
    Build the top navigation bar and attach it to *window*.
    Returns the header Frame.
    """
    hdr = tk.Frame(window, bg=BG_DARK, height=HDR_H)
    hdr.pack(fill="x")
    hdr.pack_propagate(False)

    inner = tk.Frame(hdr, bg=BG_DARK)
    inner.pack(fill="both", expand=True, padx=SIDE_PAD)

    # ── Left: accent pipe + title ─────────────────────────────────
    left = tk.Frame(inner, bg=BG_DARK)
    left.pack(side="left", fill="y", pady=10)

    tk.Frame(left, bg=accent, width=4).pack(
        side="left", fill="y", pady=4, padx=(0, 14))

    titles_frame = tk.Frame(left, bg=BG_DARK)
    titles_frame.pack(side="left", fill="y")

    tk.Label(titles_frame, text=title,
             font=F_H1, fg=TEXT_WHITE, bg=BG_DARK
             ).pack(anchor="w")
    tk.Label(titles_frame, text=subtitle,
             font=F_SMALL, fg=TEXT_OFFWHITE, bg=BG_DARK
             ).pack(anchor="w", pady=(1, 0))

    # ── Right: user chip + close button ──────────────────────────
    right = tk.Frame(inner, bg=BG_DARK)
    right.pack(side="right", fill="y", pady=12)

    # user chip
    chip = tk.Frame(right, bg=BG_MEDIUM, padx=12, pady=5)
    chip.pack(side="left", anchor="center")
    tk.Label(chip, text=f"  {username}",
             font=F_SMALL, fg=TEXT_OFFWHITE, bg=BG_MEDIUM
             ).pack()

    if on_close:
        close_btn = tk.Button(right, text="  ✕  ",
                              font=F_SMALL_B,
                              bg=RED, fg=TEXT_WHITE,
                              border=0, padx=10, pady=6,
                              cursor="hand2",
                              activebackground=RED_H,
                              activeforeground=TEXT_WHITE,
                              command=on_close)
        close_btn.pack(side="left", padx=(10, 0), anchor="center")
        _hover(close_btn, RED_H, RED)

    # ── Accent underline ─────────────────────────────────────────
    tk.Frame(window, bg=accent, height=3).pack(fill="x")

    return hdr


# ══════════════════════════════════════════════════════════════════
# STEP INDICATOR FACTORY
# ══════════════════════════════════════════════════════════════════
def build_step_indicator(window,
                         steps: list,
                         current: int,
                         accent: str = INDIGO) -> tk.Frame:
    """
    Premium horizontal step indicator with connected circles.
    steps   : list[str]  – step labels
    current : int        – 1-based index of active step
    """
    # remove any previous step bar
    for w in window.winfo_children():
        if getattr(w, "_step_bar", False):
            w.destroy()

    outer = tk.Frame(window, bg=BG_CARD, height=STEP_H)
    outer.pack(fill="x")
    outer.pack_propagate(False)
    outer._step_bar = True

    container = tk.Frame(outer, bg=BG_CARD)
    container.pack(expand=True)

    n = len(steps)
    for i, label in enumerate(steps, 1):
        done   = i < current
        active = i == current

        grp = tk.Frame(container, bg=BG_CARD)
        grp.pack(side="left")

        # connector line before each step (except first)
        if i > 1:
            line_col = accent if (done or active) else BORDER
            tk.Frame(grp, bg=line_col, width=50, height=2
                     ).pack(side="left", anchor="center")

        # circle
        if done:
            c_bg, c_fg, c_txt = accent, TEXT_WHITE, "✓"
        elif active:
            c_bg, c_fg, c_txt = accent, TEXT_WHITE, str(i)
        else:
            c_bg, c_fg, c_txt = BG_INPUT, TEXT_GHOST, str(i)

        circle = tk.Label(grp, text=c_txt,
                          font=F_SMALL_B,
                          bg=c_bg, fg=c_fg,
                          width=3, height=1,
                          relief="flat",
                          padx=2, pady=4)
        circle.pack(side="left", anchor="center")

        # label
        lbl_col = TEXT_DARK  if active else \
                  TEXT_MUTED if done   else TEXT_GHOST
        lbl_fw  = "bold" if active else "normal"
        tk.Label(grp, text=f"  {label}",
                 font=(FF, 9, lbl_fw),
                 fg=lbl_col, bg=BG_CARD
                 ).pack(side="left", anchor="center", padx=(0, 6))

    # thin divider under the bar
    tk.Frame(window, bg=BORDER, height=1).pack(fill="x")

    return outer


# ══════════════════════════════════════════════════════════════════
# REUSABLE WIDGET FACTORIES
# ══════════════════════════════════════════════════════════════════
def primary_btn(parent, text, command,
                color=INDIGO, hover_color=INDIGO_H,
                **kw) -> tk.Button:
    btn = tk.Button(parent, text=text, command=command,
                    font=F_BODY_B, bg=color, fg=TEXT_WHITE,
                    border=0, padx=22, pady=10,
                    cursor="hand2",
                    activebackground=hover_color,
                    activeforeground=TEXT_WHITE,
                    **kw)
    _hover(btn, hover_color, color)
    return btn


def ghost_btn(parent, text, command, **kw) -> tk.Button:
    btn = tk.Button(parent, text=text, command=command,
                    font=F_BODY, bg=SLATE, fg=TEXT_WHITE,
                    border=0, padx=18, pady=9,
                    cursor="hand2",
                    activebackground=SLATE_H,
                    activeforeground=TEXT_WHITE,
                    **kw)
    _hover(btn, SLATE_H, SLATE)
    return btn


def outline_btn(parent, text, command, color=INDIGO, **kw) -> tk.Button:
    btn = tk.Button(parent, text=text, command=command,
                    font=F_BODY, bg=BG_CARD, fg=color,
                    border=1, padx=18, pady=8,
                    cursor="hand2",
                    relief="solid",
                    highlightbackground=color,
                    activebackground=S_INFO_BG,
                    activeforeground=color,
                    **kw)
    return btn


def form_entry(parent, **kw) -> tk.Entry:
    e = tk.Entry(parent,
                 font=F_BODY,
                 relief="flat", bd=0,
                 bg=BG_INPUT, fg=TEXT_DARK,
                 insertbackground=INDIGO,
                 **kw)
    e.bind("<FocusIn>",  lambda ev: ev.widget.config(bg=BG_INPUT_FOC))
    e.bind("<FocusOut>", lambda ev: ev.widget.config(bg=BG_INPUT))
    return e


def search_bar(parent, textvariable, on_search, placeholder="ค้นหา...",
               accent=INDIGO) -> tk.Frame:
    """Search input + button row."""
    wrap = tk.Frame(parent,
                    bg=BG_CARD,
                    highlightbackground=BORDER,
                    highlightthickness=1)
    wrap.pack(fill="x")

    entry = tk.Entry(wrap, textvariable=textvariable,
                     font=F_BODY,
                     relief="flat", bd=0,
                     bg=BG_CARD, fg=TEXT_DARK,
                     insertbackground=accent)
    entry.pack(side="left", fill="x", expand=True, ipady=9, ipadx=12)
    entry.bind("<Return>", lambda e: on_search())
    entry.bind("<FocusIn>",  lambda e: wrap.config(highlightbackground=BORDER_FOCUS))
    entry.bind("<FocusOut>", lambda e: wrap.config(highlightbackground=BORDER))

    btn = tk.Button(wrap, text="🔍  ค้นหา",
                    font=F_SMALL_B,
                    bg=accent, fg=TEXT_WHITE,
                    border=0, padx=14, pady=0,
                    cursor="hand2",
                    activebackground=_darken(accent),
                    command=on_search)
    btn.pack(side="right", fill="y", padx=(0, 0))
    _hover(btn, _darken(accent), accent)

    return wrap


def card(parent, padx=24, pady=20, **kw) -> tk.Frame:
    """White card with subtle border."""
    return tk.Frame(parent, bg=BG_CARD,
                    highlightbackground=BORDER,
                    highlightthickness=1,
                    padx=padx, pady=pady,
                    **kw)


def section_header(parent, text: str, bg=BG_PAGE) -> tk.Frame:
    """Labelled horizontal rule inside content areas."""
    f = tk.Frame(parent, bg=bg)
    tk.Label(f, text=text, font=F_H3,
             fg=TEXT_MED, bg=bg).pack(side="left")
    tk.Frame(f, bg=BORDER, height=1).pack(
        side="left", fill="x", expand=True, padx=(10, 0), pady=6)
    return f


def kpi_card(parent, label: str, value: str,
             accent: str = INDIGO) -> tk.Frame:
    """Mini KPI tile for summary bars."""
    f = tk.Frame(parent, bg=BG_CARD,
                 highlightbackground=BORDER, highlightthickness=1,
                 padx=18, pady=12)
    tk.Frame(f, bg=accent, height=3).pack(fill="x", pady=(0, 8))
    tk.Label(f, text=label, font=F_SMALL, fg=TEXT_MUTED, bg=BG_CARD
             ).pack(anchor="w")
    tk.Label(f, text=value, font=F_H2, fg=TEXT_DARK, bg=BG_CARD
             ).pack(anchor="w")
    return f


def badge(parent, text: str, bg: str, fg: str = TEXT_WHITE) -> tk.Label:
    return tk.Label(parent, text=f"  {text}  ",
                    font=F_CAPTION, bg=bg, fg=fg, padx=2, pady=3)


def divider(parent, bg=BG_PAGE) -> tk.Frame:
    return tk.Frame(parent, bg=BORDER, height=1)


def page_title(parent, text: str, subtitle: str = "", bg=BG_PAGE):
    """Section page title used at the top of content areas."""
    f = tk.Frame(parent, bg=bg)
    tk.Label(f, text=text, font=F_H2,
             fg=TEXT_DARK, bg=bg).pack(anchor="w")
    if subtitle:
        tk.Label(f, text=subtitle, font=F_SMALL,
                 fg=TEXT_MUTED, bg=bg).pack(anchor="w", pady=(2, 0))
    return f


# ══════════════════════════════════════════════════════════════════
# TREEVIEW HELPERS
# ══════════════════════════════════════════════════════════════════
def styled_tree(parent, columns: list, headers: dict,
                widths: dict, height=14,
                accent=INDIGO) -> tuple:
    """
    Create a Premium.Treeview + Premium.Vertical.TScrollbar pair.
    Returns (tree, scrollbar).
    """
    configure_styles()

    wrap = tk.Frame(parent, bg=BG_CARD,
                    highlightbackground=BORDER, highlightthickness=1)
    wrap.pack(fill="both", expand=True)

    tree = ttk.Treeview(wrap, columns=columns,
                         show="headings",
                         style="Premium.Treeview",
                         height=height)

    for col in columns:
        anchor = "e" if col.endswith(("Amount", "Total", "Qty", "Count")) \
                     else "w"
        tree.heading(col, text=headers.get(col, col))
        tree.column(col, width=widths.get(col, 120),
                    anchor=anchor, stretch=False)

    # alternating row tags
    tree.tag_configure("odd",  background=BG_CARD)
    tree.tag_configure("even", background=BG_ROW_ALT)

    sb = ttk.Scrollbar(wrap, orient="vertical",
                        command=tree.yview,
                        style="Premium.Vertical.TScrollbar")
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")

    return tree, sb


def tree_insert(tree, values, tag=None):
    """Insert a row with alternating-stripe tag."""
    idx = len(tree.get_children())
    auto_tag = "even" if idx % 2 == 0 else "odd"
    tree.insert("", "end", values=values, tags=(tag or auto_tag,))


# ══════════════════════════════════════════════════════════════════
# WINDOW HELPERS
# ══════════════════════════════════════════════════════════════════
def center_window(win, w=WIN_W, h=WIN_H):
    win.update_idletasks()
    x = (win.winfo_screenwidth()  // 2) - (w // 2)
    y = (win.winfo_screenheight() // 2) - (h // 2)
    win.geometry(f"{w}x{h}+{x}+{y}")


def setup_toplevel(win, title: str, w=WIN_W, h=WIN_H):
    win.title(title)
    win.configure(bg=BG_PAGE)
    center_window(win, w, h)


# ══════════════════════════════════════════════════════════════════
# INTERNAL HELPERS
# ══════════════════════════════════════════════════════════════════
def _hover(widget, hover_bg: str, normal_bg: str):
    widget.bind("<Enter>", lambda e: widget.config(bg=hover_bg))
    widget.bind("<Leave>", lambda e: widget.config(bg=normal_bg))


def _darken(hex_color: str) -> str:
    """Return a slightly darker shade of a hex colour (naïve)."""
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    factor = 0.85
    r = max(0, int(r * factor))
    g = max(0, int(g * factor))
    b = max(0, int(b * factor))
    return f"#{r:02x}{g:02x}{b:02x}"
