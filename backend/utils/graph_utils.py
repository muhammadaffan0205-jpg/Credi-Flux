# backend/utils/graph_utils.py
import math
import tkinter as tk
from config import PALETTE
from typing import List, Tuple

_NODE_COLOURS = [
    "#3FB950", "#58A6FF", "#E3B341", "#FF7B72",
    "#D2A8FF", "#79C0FF", "#00C896", "#F0883E",
]

def draw_debt_graph(canvas: tk.Canvas, settlements: List[Tuple[str, str, float]],
                    current_username: str = None, width: int = None, height: int = None) -> None:
    # This is for tkinter only – not used in web version. Kept for compatibility.
    pass