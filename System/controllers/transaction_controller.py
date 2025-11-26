import customtkinter as ctk
from db import query

class TransactionController:
    def __init__(self, app):
        self.app = app

    def show_transactions(self):
        self.app.window_manager.clear_container()

        # Main Container
        frame = ctk.CTkScrollableFrame(self.app.container, corner_radius=10)
        frame.pack(pady=15, padx=15, expand=True, fill="both")

        ctk.CTkLabel(frame, text="Transaction History", font=("Arial", 26, "bold")).pack(pady=15)

        # Updated Query to fetch full billing details
        rows = query("""
            SELECT 
                p.payment_id, 
                p.payment_method, 
                p.amount as pay_amount, 
                p.payment_date, 
                c.full_name, 
                b.billing_id, 
                b.reservation_id,
                b.service_charges,
                b.discount_amount,
                b.compensation,
                b.final_amount,
                b.cashier_name
            FROM payment p
            JOIN customer c ON p.customer_id = c.customer_id
            JOIN billing b ON p.billing_id = b.billing_id
            ORDER BY p.payment_date DESC
        """, fetchall=True)

        if not rows:
            ctk.CTkLabel(frame, text="No transactions found.", font=("Arial", 16)).pack(pady=20)
        else:
            for r in rows:
                # --- CARD CONTAINER ---
                card = ctk.CTkFrame(frame, fg_color=("gray85", "gray25"), corner_radius=8, border_width=1, border_color="gray50")
                card.pack(fill='x', pady=8, padx=10)

                # --- HEADER ---
                header = ctk.CTkFrame(card, fg_color="transparent")
                header.pack(fill='x', padx=15, pady=(10,5))
                
                ctk.CTkLabel(header, text=f"Payment #{r['payment_id']}  |  {r['payment_date']}", font=("Arial", 16, "bold")).pack(side="left")
                ctk.CTkLabel(header, text=f"Res #{r['reservation_id']}", font=("Arial", 16, "bold"), text_color="gray70").pack(side="right")

                # --- SEPARATOR ---
                ctk.CTkFrame(card, height=2, fg_color="gray60").pack(fill="x", padx=10, pady=5)

                # --- BODY ---
                body = ctk.CTkFrame(card, fg_color="transparent")
                body.pack(fill='x', padx=15, pady=5)
                
                # Left: Customer & Cashier
                left = ctk.CTkFrame(body, fg_color="transparent")
                left.pack(side="left", fill="both", expand=True)
                
                cashier = r['cashier_name'] if r['cashier_name'] else "Admin Cashier"
                ctk.CTkLabel(left, text=f"Customer: {r['full_name']}", font=("Arial", 14, "bold"), anchor="w").pack(fill="x")
                ctk.CTkLabel(left, text=f"Processed by: {cashier}", font=("Arial", 13), anchor="w").pack(fill="x")
                ctk.CTkLabel(left, text=f"Method: {r['payment_method']}", font=("Arial", 13), anchor="w").pack(fill="x")

                # Right: Financial Breakdown
                right = ctk.CTkFrame(body, fg_color="transparent")
                right.pack(side="right", fill="y")
                
                # Financial Values
                subtotal = r['service_charges'] if r['service_charges'] else 0.0
                discount = r['discount_amount'] if r['discount_amount'] else 0.0
                comp = r['compensation'] if r['compensation'] else 0.0
                # Payment Amount for THIS transaction
                pay_amt = r['pay_amount'] if r['pay_amount'] else 0.0
                
                # Display Logic
                ctk.CTkLabel(right, text=f"Bill Subtotal: ₱{subtotal:,.2f}", font=("Arial", 12), anchor="e").pack(fill="x")
                if discount > 0:
                    ctk.CTkLabel(right, text=f"Discount: -₱{discount:,.2f}", font=("Arial", 12), text_color="#e67e22", anchor="e").pack(fill="x")
                if comp > 0:
                    ctk.CTkLabel(right, text=f"Compensation: -₱{comp:,.2f}", font=("Arial", 12), text_color="#e74c3c", anchor="e").pack(fill="x")
                
                ctk.CTkLabel(right, text=f"PAID NOW: ₱{pay_amt:,.2f}", font=("Arial", 16, "bold"), text_color="#27ae60", anchor="e").pack(fill="x", pady=(5,0))

        ctk.CTkButton(frame, text="Back", font=("Arial", 15, "bold"), height=40, command=self.app.admin_dashboard.show_admin_interface).pack(pady=20)