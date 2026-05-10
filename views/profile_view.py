# crediflux/views/profile_view.py
import tkinter as tk
from tkinter import messagebox
from views.widgets import label, btn, ghost_btn, Card, entry, separator
from managers.auth_manager import AuthManager
from managers.transaction_manager import TransactionManager
from config import PALETTE


class ProfileView:
    def __init__(self, parent, user, on_back, status_callback):
        self.parent = parent
        self.user = user
        self.on_back = on_back
        self.status = status_callback
        self.auth_manager = AuthManager()
        self.transaction_manager = TransactionManager()
        self.build_ui()

    def build_ui(self):
        for widget in self.parent.winfo_children():
            widget.destroy()

        top = tk.Frame(self.parent, bg=PALETTE["bg"])
        top.pack(fill="x", padx=20, pady=(10, 0))
        ghost_btn(top, "← Back to Dashboard", self.on_back).pack(side="left")
        label(top, "Profile Settings", size=18, bold=True).pack(side="left", padx=20)

        main = tk.Frame(self.parent, bg=PALETTE["bg"])
        main.pack(fill="both", expand=True, padx=20, pady=20)

        info_card = Card(main)
        info_card.pack(fill="x", pady=(0,20))
        label(info_card, "Personal Information", size=14, bold=True).pack(anchor="w")

        fields = [
            ("Full Name", self.user.full_name),
            ("Username", self.user.username),
            ("Phone", self.user.phone),
            ("EasyPaisa Number", self.user.easypaisa_num or "Not set"),
        ]
        for i, (field, value) in enumerate(fields):
            row = tk.Frame(info_card, bg=PALETTE["bg2"])
            row.pack(fill="x", pady=(0,8))
            label(row, f"{field}:", width=15, anchor="w").pack(side="left")
            if field == "EasyPaisa Number":
                self.ep_var = tk.StringVar(value=value if value else "")
                ep_entry = entry(row, textvariable=self.ep_var, width=30)
                ep_entry.pack(side="left", fill="x", expand=True)
                btn(row, "Update", self.update_easypaisa, color=PALETTE["green"], padx=10, pady=3).pack(side="right")
            else:
                value_lbl = label(row, str(value), size=11, color=PALETTE["text2"])
                value_lbl.pack(side="left", padx=(10,0))

        separator(info_card).pack(fill="x", pady=10)

        owes, owed = self.transaction_manager.get_totals(self.user.user_id)
        stats_frame = tk.Frame(info_card, bg=PALETTE["bg2"])
        stats_frame.pack(fill="x")
        label(stats_frame, "You Owe:", bold=True).pack(side="left", padx=(0,20))
        label(stats_frame, f"Rs.{owes:,.2f}", color=PALETTE["red"]).pack(side="left", padx=(0,40))
        label(stats_frame, "You Are Owed:", bold=True).pack(side="left", padx=(0,20))
        label(stats_frame, f"Rs.{owed:,.2f}", color=PALETTE["green"]).pack(side="left")

    def update_easypaisa(self):
        new_number = self.ep_var.get().strip()
        if not new_number:
            messagebox.showerror("Error", "Enter EasyPaisa number")
            return
        success, msg = self.auth_manager.update_easypaisa(self.user.user_id, new_number)
        if success:
            self.user.easypaisa_num = new_number
            self.status("EasyPaisa number updated")
            messagebox.showinfo("Success", msg)
        else:
            self.status(msg)