# crediflux/views/settlements_content.py
import tkinter as tk
from tkinter import ttk
from managers.expense_manager import ExpenseManager
from managers.group_manager import GroupManager
from views.widgets import Card, label, btn
from utils.graph_utils import draw_debt_graph
from config import PALETTE


class SettlementsContent(tk.Frame):
    def __init__(self, parent, user, status_callback):
        super().__init__(parent, bg=PALETTE["bg"])
        self.user = user
        self.status = status_callback
        self.expense_manager = ExpenseManager()
        self.group_manager = GroupManager()
        self.build_ui()
        self.load_settlements()

    def build_ui(self):
        top = tk.Frame(self, bg=PALETTE["bg"])
        top.pack(fill="x", padx=30, pady=20)
        label(top, "Select Group:", size=12).pack(side="left")
        self.group_var = tk.StringVar()
        self.group_combo = ttk.Combobox(top, textvariable=self.group_var, state="readonly", width=30)
        self.group_combo.pack(side="left", padx=10)
        btn(top, "Show", self.load_settlements, color=PALETTE["blue"]).pack(side="left")

        self.content_card = Card(self)
        self.content_card.pack(fill="both", expand=True, padx=30, pady=(0,20))

    def load_settlements(self):
        groups = self.group_manager.get_user_groups(self.user.user_id)
        if not groups:
            for w in self.content_card.winfo_children():
                w.destroy()
            label(self.content_card, "You have no groups yet.").pack()
            return
        group_names = [g.group_name for g in groups]
        self.group_combo['values'] = group_names
        if not self.group_var.get() and group_names:
            self.group_var.set(group_names[0])
        selected_name = self.group_var.get()
        group = next((g for g in groups if g.group_name == selected_name), groups[0])
        settlements = self.expense_manager.get_balance_summary(group.group_id)

        for w in self.content_card.winfo_children():
            w.destroy()

        canvas = tk.Canvas(self.content_card, bg=PALETTE["bg2"], height=300)
        canvas.pack(fill="x", pady=10)
        draw_debt_graph(canvas, settlements, current_username=self.user.username,
                        width=self.content_card.winfo_width() or 500, height=280)

        tree = ttk.Treeview(self.content_card, columns=("Debtor","Creditor","Amount"), show="headings", height=6)
        for col in ("Debtor","Creditor","Amount"):
            tree.heading(col, text=col)
            tree.column(col, width=120)
        tree.pack(fill="both", expand=True, pady=10)
        for d,c,a in settlements:
            tree.insert("", "end", values=(d, c, f"Rs.{a:,.0f}"))
        self.status(f"Showing settlements for {group.group_name}")