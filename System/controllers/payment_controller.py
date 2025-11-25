import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime
from db import query, execute

class PaymentController:
    def __init__(self, app):
        self.app = app

    def show_make_payment(self):
        if not hasattr(self.app, 'current_customer') or not self.app.current_customer:
            messagebox.showerror("Error", "No customer loaded.")
            return
            
        self.app.window_manager.clear_container()
        
        frame = ctk.CTkScrollableFrame(self.app.container)
        frame.pack(pady=12, padx=12, expand=True, fill="both")
        
        ctk.CTkLabel(frame, text="Make a Payment", font=("Helvetica", 22)).pack(pady=8)
        
        rows = query("""
            SELECT r.reservation_id, r.check_in_date, r.check_out_date, b.final_amount, b.status, b.billing_id, b.discount_amount
            FROM reservation r
            JOIN billing b ON b.reservation_id = r.reservation_id
            WHERE r.customer_id = ? AND b.status != 'Paid'
            ORDER BY r.check_in_date ASC
        """, (self.app.current_customer['customer_id'],), fetchall=True)
        
        if not rows:
            ctk.CTkLabel(frame, text="No unpaid reservations.").pack(pady=8)
        else:
            for r in rows:
                r_frame = ctk.CTkFrame(frame)
                r_frame.pack(fill='x', pady=4, padx=6)
                
                # Display formatted info
                disc_txt = f"(Disc: ₱{r['discount_amount']:.2f})" if r['discount_amount'] > 0 else ""
                txt = f"Res #{r['reservation_id']} | Due: ₱{r['final_amount']:.2f} {disc_txt}"
                
                ctk.CTkLabel(r_frame, text=txt).pack(side='left', padx=6)
                
                def pay_reservation(res_id=r['reservation_id'], billing_id=r['billing_id'], amount=r['final_amount']):
                    method = simpledialog.askstring("Payment", "Method (Cash, Card, E-Wallet):", parent=self.app)
                    if not method: return
                    
                    now = datetime.now().isoformat(sep=' ', timespec='seconds')
                    execute("INSERT INTO payment (billing_id, customer_id, payment_method, amount, payment_date) VALUES (?, ?, ?, ?, ?)",
                            (billing_id, self.app.current_customer['customer_id'], method, amount, now))
                    execute("UPDATE billing SET status='Paid', amount_paid=? WHERE billing_id=?", (amount, billing_id))
                    
                    messagebox.showinfo("Paid", f"Reservation #{res_id} paid.")
                    self.show_make_payment()
                
                ctk.CTkButton(r_frame, text="Pay Full", command=pay_reservation).pack(side='right', padx=6)
        
        ctk.CTkButton(frame, text="Back", command=self.app.admin_dashboard.show_admin_customer_dashboard).pack(pady=12)

    def show_receipts(self):
        if not hasattr(self.app, 'current_customer') or not self.app.current_customer:
            messagebox.showerror("Error", "No customer loaded.")
            return
            
        self.app.window_manager.clear_container()
        frame = ctk.CTkScrollableFrame(self.app.container)
        frame.pack(pady=12, padx=12, expand=True, fill="both")
        
        ctk.CTkLabel(frame, text="My Receipts / Transaction History", font=("Helvetica", 22)).pack(pady=8)
        
        # Updated query to fetch Guest demographics
        rows = query("""
            SELECT 
                r.reservation_id, r.check_in_date, r.check_out_date, 
                r.count_adults, r.count_kids, r.count_pwd, r.count_seniors,
                b.final_amount, b.discount_amount, b.service_charges,
                p.payment_method, p.payment_date
            FROM reservation r
            JOIN billing b ON b.reservation_id = r.reservation_id
            JOIN payment p ON p.billing_id = b.billing_id
            WHERE r.customer_id = ?
            ORDER BY p.payment_date DESC
        """, (self.app.current_customer['customer_id'],), fetchall=True)
        
        if not rows:
            ctk.CTkLabel(frame, text="No receipts available.").pack(pady=8)
        else:
            for r in rows:
                # Format Receipt Text
                guests_info = f"Guests: Adult({r['count_adults']}), Kid({r['count_kids']}), PWD({r['count_pwd']}), Senior({r['count_seniors']})"
                
                txt = (f"------------------------------------------------\n"
                       f"Reservation #{r['reservation_id']}  |  Date: {r['payment_date']}\n"
                       f"{guests_info}\n"
                       f"Stay: {r['check_in_date']} to {r['check_out_date']}\n"
                       f"Subtotal: ₱{r['service_charges']:.2f}\n"
                       f"Discount: -₱{r['discount_amount']:.2f}\n"
                       f"TOTAL PAID: ₱{r['final_amount']:.2f}  ({r['payment_method']})\n"
                       f"------------------------------------------------")
                
                r_frame = ctk.CTkFrame(frame)
                r_frame.pack(fill='x', pady=6, padx=6)
                ctk.CTkLabel(r_frame, text=txt, justify='left', font=("Courier", 12)).pack(anchor='w', padx=10, pady=5)
        
        ctk.CTkButton(frame, text="Back", command=self.app.admin_dashboard.show_admin_customer_dashboard).pack(pady=12)