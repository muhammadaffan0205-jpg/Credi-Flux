# crediflux/views/dashboard_content.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from views.widgets import Card, label, btn, ghost_btn, StatCard
from managers.expense_manager import ExpenseManager
from managers.settlement_manager import SettlementManager
from managers.transaction_manager import TransactionManager
from managers.group_manager import GroupManager
from managers.due_dates_manager import DueDatesManager
from managers.payment_manager import PaymentManager
from managers.debt_manager import DebtManager
from managers.payment_confirmation_manager import PaymentConfirmationManager
from utils.graph_utils import draw_debt_graph
from utils.balance_utils import get_global_balance_summary
from repositories.user_repo import UserRepo
from views.easypaisa_modal import EasyPaisaModal
from views.coming_soon import show_coming_soon
from config import PALETTE

class DashboardContent:
    def __init__(self, parent, user, status_callback):
        self.parent = parent
        self.user = user
        self.status = status_callback
        self.expense_manager = ExpenseManager()
        self.settlement_manager = SettlementManager()
        self.transaction_manager = TransactionManager()
        self.group_manager = GroupManager()
        self.due_dates_manager = DueDatesManager()
        self.payment_manager = PaymentManager()
        self.debt_manager = DebtManager()
        self.payment_confirmation_manager = PaymentConfirmationManager()
        self.build_ui()
        self.load_data()
        self.check_pending_requests()        # popup on login
        self.refresh_confirmations()

    def build_ui(self):
        # Main scrollable canvas
        self.main_canvas = tk.Canvas(self.parent, bg=PALETTE["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.parent, orient="vertical", command=self.main_canvas.yview)
        self.scrollable = tk.Frame(self.main_canvas, bg=PALETTE["bg"])
        self.scrollable.bind("<Configure>", lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all")))
        self.main_canvas.create_window((0,0), window=self.scrollable, anchor="nw")
        self.main_canvas.configure(yscrollcommand=scrollbar.set)
        self.main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Stats row
        stats_frame = tk.Frame(self.scrollable, bg=PALETTE["bg"])
        stats_frame.pack(fill="x", padx=30, pady=(20, 10))
        self.to_collect_card = StatCard(stats_frame, "TOTAL TO COLLECT", 0, PALETTE["green"])
        self.to_collect_card.pack(side="left", fill="x", expand=True, padx=(0,10))
        self.owed_card = StatCard(stats_frame, "TOTAL OWED", 0, PALETTE["red"])
        self.owed_card.pack(side="right", fill="x", expand=True, padx=(10,0))

        # Two columns
        main_row = tk.Frame(self.scrollable, bg=PALETTE["bg"])
        main_row.pack(fill="both", expand=True, padx=30, pady=10)
        main_row.grid_columnconfigure(0, weight=2)
        main_row.grid_columnconfigure(1, weight=1)

        # Left column
        left_col = tk.Frame(main_row, bg=PALETTE["bg"])
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0,10))

        # Graph card
        graph_card = Card(left_col)
        graph_card.pack(fill="both", expand=True, pady=(0,15))
        title_frame = tk.Frame(graph_card, bg=PALETTE["bg2"])
        title_frame.pack(fill="x")
        label(title_frame, "Optimized Debt Graph", size=14, bold=True).pack(side="left")
        add_btn = btn(title_frame, "+", self.show_add_debt_modal, color=PALETTE["ep_green"], padx=8, pady=2)
        add_btn.pack(side="right")
        self.canvas = tk.Canvas(graph_card, bg=PALETTE["bg2"], height=320, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, pady=10)

        # Payments card
        payment_card = Card(left_col)
        payment_card.pack(fill="both", expand=True)
        label(payment_card, "Optimized Payments", size=14, bold=True).pack(anchor="w")
        payment_canvas = tk.Canvas(payment_card, bg=PALETTE["bg2"], highlightthickness=0)
        payment_scrollbar = ttk.Scrollbar(payment_card, orient="vertical", command=payment_canvas.yview)
        self.payment_container = tk.Frame(payment_canvas, bg=PALETTE["bg2"])
        self.payment_container.bind("<Configure>", lambda e: payment_canvas.configure(scrollregion=payment_canvas.bbox("all")))
        payment_canvas.create_window((0,0), window=self.payment_container, anchor="nw")
        payment_canvas.configure(yscrollcommand=payment_scrollbar.set)
        payment_canvas.pack(side="left", fill="both", expand=True, pady=(8,0))
        payment_scrollbar.pack(side="right", fill="y")

        # Right column
        right_col = tk.Frame(main_row, bg=PALETTE["bg"])
        right_col.grid(row=0, column=1, sticky="nsew")

        # Incoming Debt Requests card
        self.request_card = Card(right_col)
        self.request_card.pack(fill="x", pady=(0,15))
        req_header = tk.Frame(self.request_card, bg=PALETTE["bg2"])
        req_header.pack(fill="x")
        label(req_header, "Incoming Debt Requests", size=14, bold=True).pack(side="left")
        refresh_req_btn = ghost_btn(req_header, "⟳", self.check_pending_requests)
        refresh_req_btn.pack(side="right")
        self.request_listbox = tk.Listbox(self.request_card, bg=PALETTE["bg3"], fg=PALETTE["text"],
                                          height=3, font=("Segoe UI", 10), relief="flat")
        self.request_listbox.pack(fill="both", expand=True, pady=(8,0))
        self.request_listbox.bind("<Double-Button-1>", self.on_request_selected)

        # Upcoming Due Dates card
        due_card = Card(right_col)
        due_card.pack(fill="x", pady=(0,15))
        label(due_card, "Upcoming Due Dates", size=14, bold=True).pack(anchor="w")
        self.due_listbox = tk.Listbox(due_card, bg=PALETTE["bg3"], fg=PALETTE["text"],
                                      height=5, font=("Segoe UI", 10), relief="flat")
        self.due_listbox.pack(fill="both", expand=True, pady=(8,0))

        # Payment Confirmations card
        self.confirm_card = Card(right_col)
        self.confirm_card.pack(fill="x", pady=(0,15))
        confirm_header = tk.Frame(self.confirm_card, bg=PALETTE["bg2"])
        confirm_header.pack(fill="x")
        label(confirm_header, "Payment Confirmations", size=14, bold=True).pack(side="left")
        refresh_conf_btn = ghost_btn(confirm_header, "⟳", self.refresh_confirmations)
        refresh_conf_btn.pack(side="right")
        self.confirm_listbox = tk.Listbox(self.confirm_card, bg=PALETTE["bg3"], fg=PALETTE["text"],
                                          height=4, font=("Segoe UI", 10), relief="flat")
        self.confirm_listbox.pack(fill="both", expand=True, pady=(8,0))
        self.confirm_listbox.bind("<Double-Button-1>", self.on_confirm_selected)

        # Recent Transactions card
        recent_card = Card(right_col)
        recent_card.pack(fill="both", expand=True)
        label(recent_card, "Recent Transactions", size=14, bold=True).pack(anchor="w")
        self.recent_tree = ttk.Treeview(recent_card, columns=("Date","Description","Amount","Paid To"),
                                        show="headings", height=6)
        for col in ("Date","Description","Amount","Paid To"):
            self.recent_tree.heading(col, text=col)
            self.recent_tree.column(col, width=90)
        self.recent_tree.pack(fill="both", expand=True, pady=(8,0))
        ghost_btn(recent_card, "View All Transactions", self.go_to_transactions).pack(pady=(5,0))

    def check_pending_requests(self):
        """Check for incoming debt requests, show popups, and update listbox."""
        pending = self.debt_manager.get_pending_requests(self.user.user_id)
        print(f"[DEBUG] Pending debt requests for {self.user.username}: {len(pending)}")
        # Show popups for each pending request (if any)
        for req in pending:
            answer = messagebox.askyesno(
                "Debt Request",
                f"{req['from_username']} wants you to pay Rs.{req['amount']:.2f}.\nAccept?"
            )
            if answer:
                if self.debt_manager.accept_request(req['id']):
                    messagebox.showinfo("Accepted", "Debt added to your balances.")
                    self.load_data()  # refresh dashboard
                else:
                    messagebox.showerror("Error", "Could not accept request.")
            else:
                self.debt_manager.reject_request(req['id'])
        # Update the listbox after processing
        self.refresh_request_listbox()

    def refresh_request_listbox(self):
        """Update the listbox with current pending requests."""
        pending = self.debt_manager.get_pending_requests(self.user.user_id)
        self.request_listbox.delete(0, tk.END)
        for req in pending:
            self.request_listbox.insert(tk.END, f"{req['from_username']} wants Rs.{req['amount']:.2f} (double‑click to respond)")

    def on_request_selected(self, event):
        """Handle double‑click on a debt request in the listbox."""
        selection = self.request_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        pending = self.debt_manager.get_pending_requests(self.user.user_id)
        if idx >= len(pending):
            return
        req = pending[idx]
        answer = messagebox.askyesno("Debt Request", f"Accept Rs.{req['amount']:.2f} from {req['from_username']}?")
        if answer:
            if self.debt_manager.accept_request(req['id']):
                messagebox.showinfo("Accepted", "Debt added to your balances.")
                self.load_data()
                self.refresh_request_listbox()
            else:
                messagebox.showerror("Error", "Could not accept request.")
        else:
            self.debt_manager.reject_request(req['id'])
            self.refresh_request_listbox()

    def refresh_confirmations(self):
        """Load pending payment confirmations where user is creditor."""
        pending = self.payment_confirmation_manager.get_pending_for_user(self.user.user_id)
        print(f"[DEBUG] Pending confirmations for {self.user.username}: {len(pending)}")
        self.confirm_listbox.delete(0, tk.END)
        for req in pending:
            self.confirm_listbox.insert(tk.END, f"{req['debtor_name']} paid Rs.{req['amount']:.2f} (double‑click to confirm)")
        self.status(f"Found {len(pending)} payment confirmations")

    def on_confirm_selected(self, event):
        selection = self.confirm_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        pending = self.payment_confirmation_manager.get_pending_for_user(self.user.user_id)
        if idx >= len(pending):
            return
        req = pending[idx]
        answer = messagebox.askyesno("Confirm Payment",
                                     f"Confirm that you received Rs.{req['amount']:.2f} from {req['debtor_name']}?")
        if answer:
            try:
                if self.payment_confirmation_manager.confirm_payment(req['id'], self.user.user_id):
                    messagebox.showinfo("Confirmed", "Payment confirmed. Debt settled.")
                    self.load_data()
                    self.refresh_confirmations()
                else:
                    messagebox.showerror("Error", "Could not confirm payment.")
            except Exception as e:
                import traceback
                traceback.print_exc()
                messagebox.showerror("Error", f"Exception: {e}")

    def load_data(self):
        settlements = get_global_balance_summary(self.user)
        self.canvas.update_idletasks()
        draw_debt_graph(self.canvas, settlements, current_username=self.user.username,
                        width=self.canvas.winfo_width(), height=self.canvas.winfo_height())
        # Update stats
        net_map = {}
        for d,c,a in settlements:
            net_map[d] = net_map.get(d,0) - a
            net_map[c] = net_map.get(c,0) + a
        total_to_collect = net_map.get(self.user.username, 0)
        total_owed = 0
        if total_to_collect < 0:
            total_owed = -total_to_collect
            total_to_collect = 0
        self.to_collect_card.update(total_to_collect)
        self.owed_card.update(total_owed)
        # Clear payment rows
        for widget in self.payment_container.winfo_children():
            widget.destroy()
        # Header
        header = tk.Frame(self.payment_container, bg=PALETTE["bg2"])
        header.pack(fill="x", pady=(0,5))
        for i, text in enumerate(["Peer", "Amount", "Action"]):
            lbl = tk.Label(header, text=text, bg=PALETTE["bg2"], fg=PALETTE["text2"],
                           font=("Segoe UI Semibold", 10), width=15, anchor="center")
            lbl.grid(row=0, column=i, padx=5, pady=2, sticky="ew")
        header.grid_columnconfigure(0, weight=2)
        header.grid_columnconfigure(1, weight=1)
        header.grid_columnconfigure(2, weight=1)
        for debtor, creditor, amount in settlements:
            if debtor == self.user.username:
                peer = creditor
                amount_text = f"Rs.{amount:,.0f}"
                action = "Pay Now"
                action_color = PALETTE["green"]
                command = lambda p=peer, a=amount: self.pay_debt(p, a)
            elif creditor == self.user.username:
                peer = debtor
                amount_text = f"Rs.{amount:,.0f}"
                action = "Request"
                action_color = PALETTE["amber"]
                command = lambda p=peer, a=amount: self.request_payment(p, a)
            else:
                continue
            row = tk.Frame(self.payment_container, bg=PALETTE["bg3"], pady=6)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=peer, bg=PALETTE["bg3"], fg=PALETTE["text"],
                     font=("Segoe UI", 10), width=15, anchor="center").grid(row=0, column=0, padx=5)
            tk.Label(row, text=amount_text, bg=PALETTE["bg3"], fg=PALETTE["amber_light"],
                     font=("Segoe UI Semibold", 10), width=15, anchor="center").grid(row=0, column=1, padx=5)
            btn_widget = tk.Button(row, text=action, bg=action_color, fg="white",
                                   font=("Segoe UI Semibold", 9), relief="flat",
                                   cursor="hand2", padx=10, pady=2, command=command)
            btn_widget.grid(row=0, column=2, padx=5)
        # Due dates
        due_list = self.due_dates_manager.get_upcoming_due_dates(self.user.user_id)
        self.due_listbox.delete(0, tk.END)
        for item in due_list:
            self.due_listbox.insert(tk.END, f"{item['description']} – {item['days_left']} days")
        # Recent transactions
        transactions = self.transaction_manager.get_history(self.user.user_id, limit=5)
        for row in self.recent_tree.get_children():
            self.recent_tree.delete(row)
        for t in transactions:
            date_str = t.txn_date.strftime("%Y-%m-%d") if t.txn_date else ""
            self.recent_tree.insert("", "end", values=(date_str, t.description[:20], f"Rs.{t.amount:,.0f}", t.paid_to))

    def pay_debt(self, creditor, amount):
        """Initiate payment: create confirmation request for creditor."""
        creditor_user = UserRepo.get_by_username(creditor)
        if not creditor_user:
            self.status(f"User '{creditor}' not found")
            return
        # Find debt details
        groups = self.group_manager.get_user_groups(self.user.user_id)
        target_settlement = None
        for g in groups:
            settlements = self.settlement_manager.get_for_group(g.group_id)
            target = next((s for s in settlements if s.debtor_name == self.user.username and s.creditor_name == creditor and not s.is_paid), None)
            if target:
                target_settlement = target
                break
        direct_debt_id = None
        if not target_settlement:
            direct_debts = self.debt_manager.get_active_debts(self.user.user_id)
            for debt in direct_debts:
                from_user = UserRepo.get_by_id(debt['from_user_id'])
                to_user = UserRepo.get_by_id(debt['to_user_id'])
                if from_user and to_user:
                    if from_user.username == self.user.username and to_user.username == creditor:
                        direct_debt_id = debt['id']
                        break
        if not target_settlement and not direct_debt_id:
            self.status("No active debt found for this peer")
            return
        def on_confirm():
            result = self.payment_confirmation_manager.request_payment(
                debtor_id=self.user.user_id,
                creditor_id=creditor_user.user_id,
                amount=amount,
                settlement_id=target_settlement.settlement_id if target_settlement else None,
                direct_debt_id=direct_debt_id
            )
            if result:
                self.status(f"Payment request sent to {creditor}. They will confirm after receiving the money.")
                print(f"[DEBUG] Created confirmation request ID {result}")
            else:
                self.status("Failed to create payment request")
        EasyPaisaModal(self.parent, creditor, amount, creditor_user.pay_number, on_confirm)

    def request_payment(self, debtor, amount):
        messagebox.showinfo("Request Payment", f"Reminder sent to {debtor} for Rs.{amount:,.0f}.\n(Notification feature coming soon)")

    def go_to_transactions(self):
        show_coming_soon(self.parent, "Full transactions list")

    def show_add_debt_modal(self):
        phone = simpledialog.askstring("Add Debt", "Enter other user's phone number:", parent=self.parent)
        if not phone: return
        amount_str = simpledialog.askstring("Amount", "Enter amount (Rs.):", parent=self.parent)
        if not amount_str: return
        try:
            amount = float(amount_str)
        except:
            messagebox.showerror("Error", "Invalid amount")
            return
        direction = messagebox.askquestion("Direction", "Are you the one who owes money?\n(Yes = You owe them, No = They owe you)")
        if direction == 'yes':
            success, msg = self.debt_manager.request_debt(self.user.user_id, phone, amount)
        else:
            other_user = UserRepo.get_by_phone(phone)
            if not other_user:
                messagebox.showerror("Error", "User not found")
                return
            success, msg = self.debt_manager.request_debt(other_user.user_id, self.user.phone, amount)
        if success:
            messagebox.showinfo("Request Sent", msg)
        else:
            messagebox.showerror("Failed", msg)