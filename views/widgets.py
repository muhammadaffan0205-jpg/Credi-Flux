# crediflux/views/widgets.py
import tkinter as tk
from tkinter import ttk
from config import PALETTE, FONT_BODY, FONT_BOLD, FONT_SMALL

def btn(parent, text, command, color=None, fg="#FFFFFF",
        font=FONT_BOLD, padx=14, pady=8, **kwargs):
    color = color or PALETTE["blue"]
    return tk.Button(
        parent, text=text, command=command,
        bg=color, fg=fg, activebackground=color, activeforeground=fg,
        relief="flat", bd=0, font=font,
        padx=padx, pady=pady, cursor="hand2", **kwargs
    )

def ghost_btn(parent, text, command, font=FONT_SMALL, **kwargs):
    return tk.Button(
        parent, text=text, command=command,
        bg=PALETTE["bg3"], fg=PALETTE["text2"],
        activebackground=PALETTE["bg4"], activeforeground=PALETTE["text"],
        relief="flat", bd=0, font=font,
        padx=12, pady=7, cursor="hand2", **kwargs
    )

def label(parent, text, size=11, bold=False, color=None, **kwargs):
    color = color or PALETTE["text"]
    weight = "Semibold" if bold else ""
    font = (f"Segoe UI {weight}".strip(), size)
    return tk.Label(parent, text=text, bg=parent["bg"],
                    fg=color, font=font, **kwargs)

def muted_label(parent, text, size=10, **kwargs):
    return label(parent, text, size=size, color=PALETTE["text2"], **kwargs)

def entry(parent, show=None, width=None, **kwargs):
    e = tk.Entry(
        parent,
        show=show,
        bg=PALETTE["bg3"],
        fg=PALETTE["text"],
        insertbackground=PALETTE["text"],
        relief="solid",
        bd=1,
        highlightthickness=1,
        highlightbackground=PALETTE["border"],
        highlightcolor=PALETTE["blue"],
        font=FONT_BODY,
        **kwargs
    )
    if width:
        e.config(width=width)
    return e

def separator(parent, color=None):
    color = color or PALETTE["border"]
    return tk.Frame(parent, bg=color, height=1)

class Card(tk.Frame):
    """Simple card – a dark frame with border."""
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            bg=PALETTE["bg2"],
            highlightthickness=1,
            highlightbackground=PALETTE["border"],
            highlightcolor=PALETTE["border"],
            padx=16,
            pady=14,
            **kwargs
        )

class StatCard(tk.Frame):
    def __init__(self, parent, title, amount, color, **kwargs):
        super().__init__(parent, bg=color, padx=20, pady=14, **kwargs)
        tk.Label(self, text=title.upper(), bg=color, fg="#FFFFFF",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.amount_var = tk.StringVar(value=f"Rs. {amount:,.0f}")
        tk.Label(self, textvariable=self.amount_var, bg=color, fg="#FFFFFF",
                 font=("Segoe UI Semibold", 22)).pack(anchor="w", pady=(4, 0))
    def update(self, amount: float):
        self.amount_var.set(f"Rs. {amount:,.0f}")

class ScrollFrame(tk.Frame):
    def __init__(self, parent, **kwargs):
        outer = tk.Frame(parent, bg=PALETTE["bg"], **kwargs)
        outer.pack(fill="both", expand=True)
        canvas = tk.Canvas(outer, bg=PALETTE["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        self.inner = tk.Frame(canvas, bg=PALETTE["bg"])
        self.inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0), window=self.inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        self._frame = outer
    def __getitem__(self, key):
        return self._frame[key]

class NavButton(tk.Button):
    def __init__(self, parent, text, icon, command, active=False, **kwargs):
        color = PALETTE["ep_green"] if active else PALETTE["bg2"]
        super().__init__(
            parent, text=f"  {icon}  {text}", command=command,
            bg=color, fg="#FFFFFF", activebackground=PALETTE["ep_green"],
            activeforeground="#FFFFFF", relief="flat", bd=0,
            font=FONT_BODY, anchor="w", padx=12, pady=10, cursor="hand2", **kwargs
        )

class StatusBar(tk.Label):
    def __init__(self, parent, **kwargs):
        self._var = tk.StringVar(value="Ready")
        super().__init__(parent, textvariable=self._var, bg=PALETTE["bg3"],
                         fg=PALETTE["text3"], font=FONT_SMALL, anchor="w", padx=14, pady=5, **kwargs)
    def set(self, msg: str):
        self._var.set(msg)

class Table(tk.Frame):
    def __init__(self, parent, columns: list, row_height=28, **kwargs):
        super().__init__(parent, bg=PALETTE["bg2"], **kwargs)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("CF.Treeview",
            background=PALETTE["bg2"], foreground=PALETTE["text"],
            fieldbackground=PALETTE["bg2"], bordercolor=PALETTE["border"],
            rowheight=row_height, font=FONT_SMALL,
        )
        style.configure("CF.Treeview.Heading",
            background=PALETTE["bg3"], foreground=PALETTE["text2"],
            font=("Segoe UI Semibold", 9), relief="flat",
        )
        style.map("CF.Treeview", background=[("selected", PALETTE["blue"])])
        self.tv = ttk.Treeview(self, columns=columns, show="headings", style="CF.Treeview", selectmode="browse")
        for col in columns:
            self.tv.heading(col, text=col)
            self.tv.column(col, anchor="w", width=100, minwidth=60)
        sb = ttk.Scrollbar(self, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
    def clear(self):
        for row in self.tv.get_children():
            self.tv.delete(row)
    def add_row(self, values: list, tag=""):
        self.tv.insert("", "end", values=values, tags=(tag,))
    def set_col_width(self, col: str, width: int):
        self.tv.column(col, width=width)
    def on_select(self, callback):
        self.tv.bind("<<TreeviewSelect>>", callback)
    def selected_values(self):
        sel = self.tv.selection()
        if not sel:
            return None
        return self.tv.item(sel[0])["values"]