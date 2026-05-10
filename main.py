# crediflux/main.py
import tkinter as tk
from tkinter import ttk
from core.db_connection import init_schema, close_db
from views.auth_view import AuthGUI
from views.dashboard_content import DashboardContent
from views.groups_content import GroupsContent
from views.transactions_view import TransactionsView
from views.settlements_content import SettlementsContent
from views.profile_view import ProfileView
from views.coming_soon import show_coming_soon
from config import PALETTE, APP_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT, MIN_WIDTH, MIN_HEIGHT

class CrediFluxApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(MIN_WIDTH, MIN_HEIGHT)
        self.root.configure(bg=PALETTE["bg"])

        self.current_user = None
        self.content_frame = None
        self.show_login()

    def show_login(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        AuthGUI(self.root, self.on_login_success)

    def on_login_success(self, user):
        self.current_user = user
        self.build_main_interface()

    def build_main_interface(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        main_panel = tk.Frame(self.root, bg=PALETTE["bg"])
        main_panel.pack(fill="both", expand=True)

        sidebar = tk.Frame(main_panel, bg=PALETTE["bg2"], width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Header frame (hamburger + logo)
        header_frame = tk.Frame(sidebar, bg=PALETTE["bg2"])
        header_frame.pack(fill="x", pady=(20, 30))

        # Hamburger icon (three lines)
        hamburger = tk.Label(header_frame, text="☰", font=("Segoe UI", 18),
                             bg=PALETTE["bg2"], fg=PALETTE["text"], cursor="hand2")
        hamburger.pack(side="left", padx=(10, 0))
        # (Optional: bind the hamburger to toggle sidebar collapse later)

        # Logo: "CREDI" white + "FLUX" green
        logo_frame = tk.Frame(header_frame, bg=PALETTE["bg2"])
        logo_frame.pack(side="left", padx=(10, 0))
        cred = tk.Label(logo_frame, text="CREDI", font=("Segoe UI Semibold", 18),
                        bg=PALETTE["bg2"], fg="white")
        cred.pack(side="left")
        flux = tk.Label(logo_frame, text="FLUX", font=("Segoe UI Semibold", 18),
                        bg=PALETTE["bg2"], fg=PALETTE["ep_green"])
        flux.pack(side="left")

        nav_items = [
            ("🏠 Dashboard", self.show_dashboard),
            ("👥 My Groups", self.show_groups),
            ("📜 Transactions", self.show_transactions),
            ("⚖️ Settlements", self.show_settlements),
            ("📊 Reports", lambda: show_coming_soon(self.root, "Reports")),
            ("👤 Profile", self.show_profile),
        ]
        for text, cmd in nav_items:
            btn = tk.Button(sidebar, text=text, command=cmd,
                            bg=PALETTE["bg2"], fg=PALETTE["text"],
                            activebackground=PALETTE["ep_green"],
                            activeforeground="white", relief="flat",
                            anchor="w", padx=20, pady=12, font=("Segoe UI", 11),
                            cursor="hand2")
            btn.pack(fill="x")

        tk.Frame(sidebar, bg=PALETTE["border"], height=1).pack(fill="x", pady=20)

        tk.Button(sidebar, text="🚪 Logout", command=self.logout,
                  bg=PALETTE["bg2"], fg=PALETTE["red_light"],
                  activebackground=PALETTE["red_bg"], activeforeground="white",
                  relief="flat", anchor="w", padx=20, pady=12, font=("Segoe UI", 11),
                  cursor="hand2").pack(fill="x", side="bottom", pady=(0, 20))

        self.content_frame = tk.Frame(main_panel, bg=PALETTE["bg"])
        self.content_frame.pack(side="right", fill="both", expand=True)

        self.show_dashboard()

    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        self.clear_content()
        DashboardContent(self.content_frame, self.current_user, self.status_bar)

    def show_groups(self):
        self.clear_content()
        GroupsContent(self.content_frame, self.current_user, self.status_bar)

    def show_transactions(self):
        self.clear_content()
        TransactionsView(self.content_frame, self.current_user, self.show_dashboard, self.status_bar)

    def show_settlements(self):
        self.clear_content()
        SettlementsContent(self.content_frame, self.current_user, self.status_bar)

    def show_profile(self):
        self.clear_content()
        ProfileView(self.content_frame, self.current_user, self.show_dashboard, self.status_bar)

    def logout(self):
        self.current_user = None
        self.show_login()

    def status_bar(self, msg):
        print(f"[STATUS] {msg}")   # can be upgraded to real status bar later

if __name__ == "__main__":
    init_schema()
    root = tk.Tk()
    app = CrediFluxApp(root)
    root.mainloop()
    close_db()
