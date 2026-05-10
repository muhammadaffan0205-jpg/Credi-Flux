# crediflux/views/auth_view.py
import tkinter as tk
from tkinter import messagebox
from managers.auth_manager import AuthManager
from views.widgets import label, entry, btn, ghost_btn, Card
from config import PALETTE, APP_TITLE

class AuthGUI:
    def __init__(self, root, on_login_success):
        self.root = root
        self.on_login_success = on_login_success
        self.root.title(f"{APP_TITLE} — Login")
        self.root.geometry("460x560")
        self.root.configure(bg=PALETTE["bg"])
        self.auth = AuthManager()
        self.main_frame = tk.Frame(self.root, bg=PALETTE["bg"], padx=24, pady=24)
        self.main_frame.pack(fill="both", expand=True)
        self.show_login_screen()

    def clear_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_login_screen(self):
        self.clear_frame()
        # Logo with split colors
        logo_frame = tk.Frame(self.main_frame, bg=PALETTE["bg"])
        logo_frame.pack(anchor="w")
        cred = tk.Label(logo_frame, text="CREDI", font=("Segoe UI Semibold", 26),
                        bg=PALETTE["bg"], fg="white")
        cred.pack(side="left")
        flux = tk.Label(logo_frame, text="FLUX", font=("Segoe UI Semibold", 26),
                        bg=PALETTE["bg"], fg=PALETTE["ep_green"])
        flux.pack(side="left")
        tk.Label(self.main_frame, text="Sign in to continue", font=("Segoe UI", 11),
                 bg=PALETTE["bg"], fg=PALETTE["text2"]).pack(anchor="w", pady=(2, 0))

        card = Card(self.main_frame)
        card.pack(fill="x", pady=(20, 0))

        tk.Label(card, text="Login", font=("Segoe UI Semibold", 20),
                 bg=PALETTE["bg2"], fg=PALETTE["text"]).pack(anchor="w", pady=(0, 12))
        label(card, "Username").pack(anchor="w")
        self.user_entry = entry(card)
        self.user_entry.pack(fill="x", pady=(6, 12))
        label(card, "Password").pack(anchor="w")
        self.pass_entry = entry(card, show="*")
        self.pass_entry.pack(fill="x", pady=(6, 16))
        btn(card, "Login", self.handle_login, color=PALETTE["green"]).pack(fill="x")

        footer = tk.Frame(card, bg=PALETTE["bg2"])
        footer.pack(fill="x", pady=(16, 0))
        tk.Label(footer, text="Don't have an account?", bg=PALETTE["bg2"],
                 fg=PALETTE["text2"], font=("Segoe UI", 10)).pack(side="left")
        ghost_btn(footer, "Register Here", self.show_register_screen,
                  font=("Segoe UI Semibold", 10)).pack(side="left", padx=(6, 0))
        self.root.bind("<Return>", lambda e: self.handle_login())

    def show_register_screen(self):
        self.clear_frame()
        logo_frame = tk.Frame(self.main_frame, bg=PALETTE["bg"])
        logo_frame.pack(anchor="w")
        cred = tk.Label(logo_frame, text="CREDI", font=("Segoe UI Semibold", 26),
                        bg=PALETTE["bg"], fg="white")
        cred.pack(side="left")
        flux = tk.Label(logo_frame, text="FLUX", font=("Segoe UI Semibold", 26),
                        bg=PALETTE["bg"], fg=PALETTE["ep_green"])
        flux.pack(side="left")
        tk.Label(self.main_frame, text="Create your account", font=("Segoe UI", 11),
                 bg=PALETTE["bg"], fg=PALETTE["text2"]).pack(anchor="w", pady=(2, 0))

        card = Card(self.main_frame)
        card.pack(fill="x", pady=(20, 0))
        tk.Label(card, text="Register", font=("Segoe UI Semibold", 20),
                 bg=PALETTE["bg2"], fg=PALETTE["text"]).pack(anchor="w", pady=(0, 12))
        label(card, "Full Name").pack(anchor="w")
        self.name_reg = entry(card)
        self.name_reg.pack(fill="x", pady=(6, 10))
        label(card, "Username").pack(anchor="w")
        self.user_reg = entry(card)
        self.user_reg.pack(fill="x", pady=(6, 10))
        label(card, "Phone Number").pack(anchor="w")
        self.phone_reg = entry(card)
        self.phone_reg.pack(fill="x", pady=(6, 10))
        label(card, "Password").pack(anchor="w")
        self.pass_reg = entry(card, show="*")
        self.pass_reg.pack(fill="x", pady=(6, 16))
        btn(card, "Sign Up", self.handle_register, color=PALETTE["blue"]).pack(fill="x")
        ghost_btn(card, "Back to Login", self.show_login_screen,
                  font=("Segoe UI", 10)).pack(pady=(12, 0))
        self.root.bind("<Return>", lambda e: self.handle_register())

    def handle_login(self):
        username = self.user_entry.get().strip()
        password = self.pass_entry.get()
        success, result = self.auth.login(username, password)
        if success:
            messagebox.showinfo("Success", f"Welcome, {result.full_name}!")
            self.on_login_success(result)
        else:
            messagebox.showerror("Login Failed", result)

    def handle_register(self):
        name = self.name_reg.get().strip()
        username = self.user_reg.get().strip()
        phone = self.phone_reg.get().strip()
        password = self.pass_reg.get()
        success, result = self.auth.register(name, username, phone, password)
        if success:
            messagebox.showinfo("Success", "Registration successful! Please login.")
            self.show_login_screen()
        else:
            messagebox.showerror("Registration Failed", result)