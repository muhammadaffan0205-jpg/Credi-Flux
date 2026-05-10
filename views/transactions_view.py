# crediflux/views/transactions_view.py
import tkinter as tk
from tkinter import ttk
from views.widgets import label, ghost_btn, Card, entry, btn
from managers.transaction_manager import TransactionManager
from config import PALETTE


class TransactionsView:
    def __init__(self, parent, user, on_back, status_callback):
        self.parent = parent
        self.user = user
        self.on_back = on_back
        self.status = status_callback
        self.transaction_manager = TransactionManager()
        self.build_ui()

    def build_ui(self):
        for widget in self.parent.winfo_children():
            widget.destroy()

        top = tk.Frame(self.parent, bg=PALETTE["bg"])
        top.pack(fill="x", padx=20, pady=(10, 0))
        ghost_btn(top, "← Back to Dashboard", self.on_back).pack(side="left")
        label(top, "Transaction History", size=18, bold=True).pack(side="left", padx=20)

        filter_card = Card(self.parent)
        filter_card.pack(fill="x", padx=20, pady=(10, 10))
        label(filter_card, "Filter", size=12, bold=True).pack(anchor="w")
        filter_frame = tk.Frame(filter_card, bg=PALETTE["bg2"])
        filter_frame.pack(fill="x", pady=(5, 0))
        label(filter_frame, "Search:").pack(side="left", padx=(0,5))
        self.search_entry = entry(filter_frame, width=30)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0,10))
        btn(filter_frame, "Apply", self.load_data, color=PALETTE["blue"], padx=10, pady=5).pack(side="left")
        ghost_btn(filter_frame, "Clear", self.clear_filter).pack(side="left", padx=(5,0))

        table_card = Card(self.parent)
        table_card.pack(fill="both", expand=True, padx=20, pady=(0,20))
        label(table_card, "Transactions", size=12, bold=True).pack(anchor="w")

        columns = ("Date", "Description", "Group", "Amount", "Paid To")
        self.tree = ttk.Treeview(table_card, columns=columns, show="headings", height=15)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="w")
        self.tree.pack(fill="both", expand=True, pady=(8,0))

        self.load_data()

    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        transactions = self.transaction_manager.get_history(self.user.user_id, limit=200)
        search_term = self.search_entry.get().strip().lower()
        for t in transactions:
            if search_term and search_term not in t.description.lower() and search_term not in (t.paid_to.lower() if t.paid_to else ""):
                continue
            date_str = t.txn_date.strftime("%Y-%m-%d %H:%M") if t.txn_date else ""
            group_str = str(t.group_id) if t.group_id else "—"
            self.tree.insert("", "end", values=(
                date_str,
                t.description,
                group_str,
                f"Rs.{t.amount:,.2f}",
                t.paid_to
            ))
        self.status(f"Loaded {len(self.tree.get_children())} transactions")

    def clear_filter(self):
        self.search_entry.delete(0, tk.END)
        self.load_data()