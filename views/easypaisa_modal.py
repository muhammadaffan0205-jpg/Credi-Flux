# crediflux/views/easypaisa_modal.py
import tkinter as tk
from tkinter import messagebox
from views.widgets import label, btn, Card
from utils.easypaisa_helper import EasypaisaHelper
from config import PALETTE

class EasyPaisaModal(tk.Toplevel):
    def __init__(self, parent, creditor_name, amount, receiver_phone, on_confirm):
        super().__init__(parent)
        self.creditor_name = creditor_name
        self.amount = amount
        self.receiver_phone = receiver_phone
        self.on_confirm = on_confirm
        self.title("Send Payment")
        self.geometry("480x380")
        self.configure(bg=PALETTE["bg"])
        self.resizable(False, False)
        self.grab_set()

        card = Card(self)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        label(card, f"Pay Rs.{amount:,.0f} to {creditor_name}", size=16, bold=True, color=PALETTE["ep_green"]).pack(pady=(0, 15))

        # Receiver number frame
        number_frame = tk.Frame(card, bg=PALETTE["bg2"], padx=15, pady=10)
        number_frame.pack(fill="x", pady=(0, 15))
        tk.Label(number_frame, text="Receiver's payment number:", bg=PALETTE["bg2"], fg=PALETTE["text2"], font=("Segoe UI", 10)).pack(anchor="w")
        number_display = tk.Label(number_frame, text=receiver_phone, bg=PALETTE["bg3"], fg=PALETTE["text"],
                                  font=("Segoe UI", 14, "bold"), padx=10, pady=6)
        number_display.pack(fill="x", pady=(5, 10))

        # Button that changes from Copy → I've Paid
        self.action_btn = tk.Button(
            number_frame, text="📋 Copy Number", command=self.copy_number,
            bg=PALETTE["blue_light"], fg="white", font=("Segoe UI Semibold", 10),
            relief="flat", padx=10, pady=6, cursor="hand2"
        )
        self.action_btn.pack()

        # Instructions
        instructions = tk.Text(card, height=4, bg=PALETTE["bg2"], fg=PALETTE["text2"],
                               wrap="word", font=("Segoe UI", 10), relief="flat", padx=10, pady=8)
        instructions.insert("1.0", "🔹 Open EasyPaisa, JazzCash, or any banking app on your phone.\n"
                                   "🔹 Send the amount shown above to the number displayed.\n"
                                   "🔹 After completing the payment, click the button again (now green).")
        instructions.config(state="disabled")
        instructions.pack(fill="both", expand=True, pady=(0, 15))

        # Cancel button at bottom
        btn_frame = tk.Frame(card, bg=PALETTE["bg2"])
        btn_frame.pack(fill="x")
        cancel_btn = tk.Button(btn_frame, text="Cancel", command=self.destroy,
                               bg=PALETTE["border"], fg=PALETTE["text"], font=("Segoe UI", 10),
                               relief="flat", padx=20, pady=6, cursor="hand2")
        cancel_btn.pack(side="right")

    def copy_number(self):
        """Copy number to clipboard, then change button to I've Paid (green)."""
        self.clipboard_clear()
        self.clipboard_append(self.receiver_phone)
        self.update()
        messagebox.showinfo("Copied", f"Number {self.receiver_phone} copied to clipboard.\n"
                            "Now open your payment app and send the amount.\n"
                            "Then click the green button below.")
        # Change button appearance and command
        self.action_btn.config(text="✓ I've Paid", bg=PALETTE["green"], command=self.confirm_payment)

    def confirm_payment(self):
        """Called when user clicks I've Paid."""
        self.on_confirm()
        self.destroy()