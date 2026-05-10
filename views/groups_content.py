# crediflux/views/groups_content.py
import tkinter as tk
from views.group_view import GroupGUI
from managers.group_manager import GroupManager
from views.widgets import label, btn, entry, ghost_btn
from config import PALETTE

class GroupsContent(tk.Frame):
    def __init__(self, parent, user, status_callback):
        super().__init__(parent, bg=PALETTE["bg"])
        self.user = user
        self.status = status_callback
        self.group_manager = GroupManager()
        self.build_ui()
        self.load_groups()

    def build_ui(self):
        # Left panel (simple frame, no Card)
        self.left_frame = tk.Frame(self, bg=PALETTE["bg2"], width=280)
        self.left_frame.pack(side="left", fill="both", expand=False)
        self.left_frame.pack_propagate(False)

        # Create group area
        create_frame = tk.Frame(self.left_frame, bg=PALETTE["bg2"])
        create_frame.pack(fill="x", pady=(10,5))
        label(create_frame, "Create New Group", size=12, bold=True).pack(anchor="w")
        entry_frame = tk.Frame(create_frame, bg=PALETTE["bg2"])
        entry_frame.pack(fill="x", pady=(5,0))
        self.new_group_entry = entry(entry_frame, width=20)
        self.new_group_entry.pack(side="left", fill="x", expand=True)
        btn(entry_frame, "+", self.create_group, color=PALETTE["green"], padx=10).pack(side="right", padx=(5,0))

        # Groups list
        label(self.left_frame, "My Groups", size=12, bold=True).pack(anchor="w", pady=(10,0))
        self.group_listbox = tk.Listbox(self.left_frame, bg=PALETTE["bg3"], fg=PALETTE["text"],
                                        height=15, font=("Segoe UI", 11))
        self.group_listbox.pack(fill="both", expand=True, pady=(5,10))
        self.group_listbox.bind("<<ListboxSelect>>", self.on_select_group)

        # Right panel
        self.right_frame = tk.Frame(self, bg=PALETTE["bg"])
        self.right_frame.pack(side="right", fill="both", expand=True, padx=(10,20), pady=20)
        self.show_placeholder()

    def show_placeholder(self):
        for w in self.right_frame.winfo_children():
            w.destroy()
        label(self.right_frame, "Select a group to manage", size=14, color=PALETTE["text2"]).pack(expand=True)

    def load_groups(self):
        self.group_listbox.delete(0, tk.END)
        self.groups = self.group_manager.get_user_groups(self.user.user_id)
        if not self.groups:
            self.group_listbox.insert(tk.END, "No groups yet. Create one above.")
        else:
            for g in self.groups:
                self.group_listbox.insert(tk.END, f"{g.group_name} ({g.member_count} members)")

    def on_select_group(self, event):
        sel = self.group_listbox.curselection()
        if not sel or not self.groups:
            return
        idx = sel[0]
        if idx >= len(self.groups):
            return
        group = self.groups[idx]
        self.show_group_detail(group)

    def show_group_detail(self, group):
        for w in self.right_frame.winfo_children():
            w.destroy()
        GroupGUI(self.right_frame, self.user, group, self.back_to_list, self.status)

    def back_to_list(self):
        self.load_groups()
        self.show_placeholder()

    def create_group(self):
        name = self.new_group_entry.get().strip()
        if not name:
            self.status("Enter group name")
            return
        group = self.group_manager.create(name, self.user.user_id)
        if group:
            self.new_group_entry.delete(0, tk.END)
            self.load_groups()
            self.status(f"Group '{name}' created")
        else:
            self.status("Failed to create group")