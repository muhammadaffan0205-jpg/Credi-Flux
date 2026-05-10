# crediflux/utils/graph_utils.py
import math
import tkinter as tk
from config import PALETTE
from typing import List, Tuple

_NODE_COLOURS = [
    "#3FB950", "#58A6FF", "#E3B341", "#FF7B72",
    "#D2A8FF", "#79C0FF", "#00C896", "#F0883E",
]

def draw_debt_graph(
    canvas: tk.Canvas,
    settlements: List[Tuple[str, str, float]],
    current_username: str = None,
    width: int = None,
    height: int = None,
) -> None:
    """
    Draws the debt graph.
    - settlements: list of (debtor, creditor, amount)
    - current_username: if provided, that node gets a white ring and label "You"
    """
    canvas.delete("all")
    
    # Get canvas dimensions if not provided
    if width is None or height is None:
        canvas.update_idletasks()
        width = canvas.winfo_width()
        height = canvas.winfo_height()
    
    # Fallback if too small
    if width < 100:
        width = 500
    if height < 100:
        height = 300

    if not settlements:
        canvas.create_text(
            width // 2, height // 2,
            text="No debts — all settled!",
            fill=PALETTE["text2"],
            font=("Segoe UI", 13)
        )
        return

    # Collect unique names
    names = []
    for debtor, creditor, _ in settlements:
        if debtor not in names:
            names.append(debtor)
        if creditor not in names:
            names.append(creditor)
    
    n = len(names)
    cx, cy = width // 2, height // 2
    radius = min(cx, cy) - 55
    if radius < 50:
        radius = min(cx, cy) - 20
    
    # Place nodes in a circle
    positions = {}
    for i, name in enumerate(names):
        angle = (2 * math.pi * i / n) - math.pi / 2
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        positions[name] = (x, y)
    
    node_r = 26
    colour_map = {name: _NODE_COLOURS[i % len(_NODE_COLOURS)] for i, name in enumerate(names)}
    
    # Draw edges (arrows)
    for debtor, creditor, amount in settlements:
        x1, y1 = positions[debtor]
        x2, y2 = positions[creditor]
        dx, dy = x2 - x1, y2 - y1
        dist = math.hypot(dx, dy)
        if dist == 0:
            continue
        ux, uy = dx / dist, dy / dist
        sx, sy = x1 + ux * node_r, y1 + uy * node_r
        ex, ey = x2 - ux * node_r, y2 - uy * node_r
        
        canvas.create_line(
            sx, sy, ex, ey,
            arrow=tk.LAST, arrowshape=(10,14,5),
            fill=PALETTE["ep_green"], width=2, smooth=True,
        )
        mx, my = (sx + ex) / 2, (sy + ey) / 2
        off_x = -uy * 14
        off_y = ux * 14
        canvas.create_text(
            mx + off_x, my + off_y,
            text=f"Rs.{amount:,.0f}",
            fill=PALETTE["amber_light"],
            font=("Segoe UI", 9, "bold"),
        )
    
    # Draw nodes
    for name, (x, y) in positions.items():
        colour = colour_map[name]
        # Shadow
        canvas.create_oval(
            x - node_r + 2, y - node_r + 2, x + node_r + 2, y + node_r + 2,
            fill="#000000", outline="", stipple="gray25"
        )
        # Main circle
        canvas.create_oval(
            x - node_r, y - node_r, x + node_r, y + node_r,
            fill=colour, outline=PALETTE["bg2"], width=2
        )
        # White ring for logged‑in user
        if current_username and name == current_username:
            canvas.create_oval(
                x - node_r - 2, y - node_r - 2, x + node_r + 2, y + node_r + 2,
                outline="#FFFFFF", width=2, fill=""
            )
        # Label inside circle
        if current_username and name == current_username:
            label_text = "You"
        else:
            label_text = "".join(w[0].upper() for w in name.split()[:2])
        canvas.create_text(x, y, text=label_text, fill="#FFFFFF", font=("Segoe UI Semibold", 11))
        
        # Full name below circle (for current user also shows "You")
        display_name = "You" if (current_username and name == current_username) else name
        canvas.create_text(
            x, y + node_r + 14,
            text=display_name,
            fill=PALETTE["text"],
            font=("Segoe UI", 9),
        )

    canvas.configure(scrollregion=canvas.bbox("all"))