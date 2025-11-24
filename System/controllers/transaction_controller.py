# transaction_controller.py

import customtkinter as ctk
from tkinter import messagebox, simpledialog
from db import query, execute
from datetime import datetime

class TransactionController:
    def __init__(self, app):
        """
        app = reference to MainApp
        """
        self.app = app

    # ------------------------------------------------------------
    # SHOW MAKE PAYMENT
    # ------------------------------------------------------------
    def show_make_payment(self):
        if not self.app.current_customer:
            messagebox.showerror("Error", "No customer loaded.")
            return

        self.app.clear_container()
        frame = ctk.CTkScrollableFrame(self.app.container)
        frame.pack(pady=12, padx=12, expand=True, fill="both")

        ctk.CTkLabel(frame, text="Make a Payment", font=("Helvetica", 22)).pack(pady=8)

        rows = query("""
            SELECT r.reservation_id, r.check_in_date, r.check_out_date, b.final_amount, b.status, b.billing_id
            FROM reservation r
            JOIN billing b ON b.reservation_id = r.reservation_id
            WHERE r.customer_id = ? AND b.status='Unpaid'
            ORDER BY r.check_in_date ASC
        """, (self.app.current_customer['customer_id'],), fetchall=True)

        if not rows:
            ctk.CTkLabel(frame, text="No unpaid reservations.").pack(pady=8)
        else:
            for r in rows:
                r_frame = ctk.CTkFrame(frame)
                r_frame.pack(fill='x', pady=4, padx=6)
                ctk.CTkLabel(r_frame, text=f"Reservation #{r['reservation_id']} | {r['check_in_date']} to {r['check_out_date']} | ₱{r['final_amount']:.2f}").pack(side='left', padx=6)

                def pay_reservation(res_id=r['reservation_id'], billing_id=r['billing_id'], amount=r['final_amount']):
                    method = simpledialog.askstring("Payment Method", "Enter payment method (cash, e-wallet, card):", parent=self.app)
                    if not method:
                        return
                    method = method.lower()
                    if method not in ('cash','e-wallet','card'):
                        messagebox.showerror("Invalid", "Method must be cash, e-wallet, or card")
                        return
                    now = datetime.now().isoformat(sep=' ', timespec='seconds')
                    execute(
                        "INSERT INTO payment (billing_id, customer_id, payment_method, amount, payment_date) VALUES (?, ?, ?, ?, ?)",
                        (billing_id, self.app.current_customer['customer_id'], method, amount, now)
                    )
                    execute("UPDATE billing SET status='Paid' WHERE billing_id=?", (billing_id,))
                    messagebox.showinfo("Paid", f"Reservation #{res_id} paid via {method}.")
                    self.show_make_payment()

                ctk.CTkButton(r_frame, text="Pay", command=pay_reservation).pack(side='right', padx=6)

        ctk.CTkButton(frame, text="Back", command=self.app.show_admin_customer_dashboard).pack(pady=12)

    # ------------------------------------------------------------
    # SHOW RECEIPTS
    # ------------------------------------------------------------
    def show_receipts(self):
        if not self.app.current_customer:
            messagebox.showerror("Error", "No customer loaded.")
            return

        self.app.clear_container()
        frame = ctk.CTkScrollableFrame(self.app.container)
        frame.pack(pady=12, padx=12, expand=True, fill="both")

        ctk.CTkLabel(frame, text="My Receipts", font=("Helvetica", 22)).pack(pady=8)

        rows = query("""
            SELECT r.reservation_id, r.check_in_date, r.check_out_date, b.final_amount, p.payment_method, p.payment_date
            FROM reservation r
            JOIN billing b ON b.reservation_id = r.reservation_id
            JOIN payment p ON p.billing_id = b.billing_id
            WHERE r.customer_id = ? AND b.status='Paid'
            ORDER BY p.payment_date DESC
        """, (self.app.current_customer['customer_id'],), fetchall=True)

        if not rows:
            ctk.CTkLabel(frame, text="No receipts available.").pack(pady=8)
        else:
            for r in rows:
                txt = (
                    f"Reservation #{r['reservation_id']} | {r['check_in_date']} to {r['check_out_date']}\n"
                    f"Amount: ₱{r['final_amount']:.2f} | Paid via: {r['payment_method']} | Date: {r['payment_date']}"
                )
                r_frame = ctk.CTkFrame(frame)
                r_frame.pack(fill='x', pady=4, padx=6)
                ctk.CTkLabel(r_frame, text=txt, justify='left').pack(anchor='w', padx=6, pady=4)

        ctk.CTkButton(frame, text="Back", command=self.app.show_admin_customer_dashboard).pack(pady=12)
