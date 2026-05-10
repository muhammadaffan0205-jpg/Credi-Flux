# crediflux/views/group_view.py
import tkinter as tk
from views.widgets import label, muted_label, btn, ghost_btn, Card, entry
from managers.group_manager import GroupManager
from managers.expense_manager import ExpenseManager
from config import PALETTE

class GroupGUI:
    def __init__(self, parent, user, group, on_back, status_callback):
        self.parent = parent
        self.user = user
        self.group = group
        self.on_back = on_back
        self.set_status = status_callback
        self.group_manager = GroupManager()
        self.expense_manager = ExpenseManager()
        self.build_ui()

    def build_ui(self):
        for widget in self.parent.winfo_children():
            widget.destroy()

        top = tk.Frame(self.parent, bg=PALETTE["bg"])
        top.pack(fill="x", padx=20, pady=(10,0))
        ghost_btn(top, "← Back", self.on_back).pack(side="left")
        label(top, self.group.group_name, size=18, bold=True).pack(side="left", padx=20)

        content = tk.Frame(self.parent, bg=PALETTE["bg"])
        content.pack(fill="both", expand=True, padx=20, pady=20)
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)
        content.grid_columnconfigure(2, weight=1)
        content.grid_rowconfigure(0, weight=1)

        # Members card
        members_card = Card(content)
        members_card.grid(row=0, column=0, sticky="nsew", padx=(0,10))
        label(members_card, "Members", size=14, bold=True).pack(anchor="w")
        self.members_listbox = tk.Listbox(members_card, bg=PALETTE["bg3"], fg=PALETTE["text"], height=15)
        self.members_listbox.pack(fill="both", expand=True, pady=(8,10))
        add_frame = tk.Frame(members_card, bg=PALETTE["bg2"])
        add_frame.pack(fill="x", pady=(0,5))
        self.member_entry = entry(add_frame, width=20)
        self.member_entry.pack(side="left", fill="x", expand=True)
        btn(add_frame, "Add", self.add_member, color=PALETTE["blue"], padx=10, pady=5).pack(side="right")
        btn(members_card, "Remove Selected", self.remove_member, color=PALETTE["red"]).pack(fill="x", pady=(5,0))

        # Expense card
        expense_card = Card(content)
        expense_card.grid(row=0, column=1, sticky="nsew", padx=10)
        label(expense_card, "Add Expense", size=14, bold=True).pack(anchor="w")
        label(expense_card, "Description").pack(anchor="w", pady=(8,0))
        self.desc_entry = entry(expense_card)
        self.desc_entry.pack(fill="x", pady=(2,5))
        label(expense_card, "Total Amount (Rs.)").pack(anchor="w", pady=(5,0))
        self.amount_entry = entry(expense_card)
        self.amount_entry.pack(fill="x", pady=(2,5))
        label(expense_card, "Payers (select 1 or 2)").pack(anchor="w", pady=(5,0))
        self.payers_listbox = tk.Listbox(expense_card, bg=PALETTE["bg3"], fg=PALETTE["text"], selectmode=tk.MULTIPLE, height=8)
        self.payers_listbox.pack(fill="x", pady=(5,10))
        btn(expense_card, "Add Expense", self.add_expense, color=PALETTE["ep_green"]).pack(fill="x")

        # Balances card
        balance_card = Card(content)
        balance_card.grid(row=0, column=2, sticky="nsew", padx=(10,0))
        label(balance_card, "Optimized Settlements", size=14, bold=True).pack(anchor="w")
        self.balance_listbox = tk.Listbox(balance_card, bg=PALETTE["bg3"], fg=PALETTE["text"], height=18)
        self.balance_listbox.pack(fill="both", expand=True, pady=(8,10))
        btn(balance_card, "Refresh Balances", self.load_balances, color=PALETTE["blue"]).pack(fill="x")

        self.load_members()
        self.load_balances()

    def load_members(self):
        self.members_listbox.delete(0, tk.END)
        self.payers_listbox.delete(0, tk.END)
        people = self.group_manager.get_people(self.group.group_id)
        for p in people:
            self.members_listbox.insert(tk.END, p.display_name)
            self.payers_listbox.insert(tk.END, p.display_name)

    def add_member(self):
        name = self.member_entry.get().strip()
        if not name:
            self.set_status("Enter name")
            return
        success, msg = self.group_manager.add_member(self.group.group_id, name)
        if success:
            self.member_entry.delete(0, tk.END)
            self.load_members()
            self.set_status(f"Added {name}")
        else:
            self.set_status(msg)

    def remove_member(self):
        sel = self.members_listbox.curselection()
        if not sel:
            self.set_status("Select a member")
            return
        name = self.members_listbox.get(sel[0])
        people = self.group_manager.get_people(self.group.group_id)
        person = next((p for p in people if p.display_name == name), None)
        if person and self.group_manager.remove_member(self.group.group_id, person.person_id):
            self.load_members()
            self.load_balances()
            self.set_status(f"Removed {name}")
        else:
            self.set_status("Remove failed")

    def add_expense(self):
        desc = self.desc_entry.get().strip()
        amount_str = self.amount_entry.get().strip()
        sel = self.payers_listbox.curselection()
        if not desc or not amount_str:
            self.set_status("Enter description and amount")
            return
        if len(sel) < 1 or len(sel) > 2:
            self.set_status("Select 1 or 2 payers")
            return
        payer_names = [self.payers_listbox.get(i) for i in sel]
        success, msg = self.expense_manager.add(self.group.group_id, desc, amount_str, payer_names)
        if success:
            self.desc_entry.delete(0, tk.END)
            self.amount_entry.delete(0, tk.END)
            self.load_balances()
            self.set_status(msg)
        else:
            self.set_status(msg)

    def load_balances(self):
        self.balance_listbox.delete(0, tk.END)
        settlements = self.expense_manager.get_balance_summary(self.group.group_id)
        if not settlements:
            self.balance_listbox.insert(tk.END, "All settled!")
            return
        for d,c,a in settlements:
            self.balance_listbox.insert(tk.END, f"{d} → {c}: Rs.{a:,.2f}")