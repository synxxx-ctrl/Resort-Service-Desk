import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from db import query, execute
from models import CustomerModel, RoomModel

class CheckInOutController:
    def __init__(self, app):
        self.app = app

    def show_check_in_list(self):
        self.app.window_manager.clear_container()
        frame = ctk.CTkScrollableFrame(self.app.container, corner_radius=8)
        frame.pack(pady=20, padx=20, expand=True, fill="both")
        ctk.CTkLabel(frame, text="Currently Checked-in Guests", font=("Helvetica", 22)).pack(pady=10)
        
        rows = query("""
            SELECT r.reservation_id, r.check_in_date, r.check_out_date, r.num_guests, r.status, r.room_id,
                c.full_name, c.username AS customer_code, rm.room_number, b.final_amount, b.amount_paid
            FROM reservation r
            JOIN customer c ON r.customer_id = c.customer_id
            LEFT JOIN room rm ON r.room_id = rm.room_id
            LEFT JOIN billing b ON r.reservation_id = b.reservation_id
            WHERE r.status = 'Checked-in' ORDER BY r.check_in_date DESC
        """, fetchall=True)

        if not rows:
            ctk.CTkLabel(frame, text="No guests are currently checked-in.", font=("Helvetica", 16)).pack(pady=20)
        else:
            for row in rows:
                res_frame = ctk.CTkFrame(frame, corner_radius=6)
                res_frame.pack(fill='x', padx=10, pady=5)
                final_amount = row['final_amount'] if row['final_amount'] is not None else 0
                amount_paid = row['amount_paid'] if row['amount_paid'] is not None else 0
                balance_due = final_amount - amount_paid
                info = (f"ID: {row['reservation_id']} | Room: {row['room_number'] or 'N/A'} | Guests: {row['num_guests']}\n"
                        f"Customer: {row['full_name']} (Code: {row['customer_code']})\n"
                        f"Status: {row['status']} | Balance Due: ₱{balance_due:.2f}")
                ctk.CTkLabel(res_frame, text=info, justify='left').pack(side='left', padx=10, pady=10, anchor='w')
                ctk.CTkButton(res_frame, text="Check-out & Bill", command=lambda res_id=row['reservation_id'], room_num=row['room_number'], r_id=row['room_id']: self.show_check_out_process(res_id, room_num, r_id)).pack(side='right', padx=10, pady=10)
        ctk.CTkButton(frame, text="Back to Admin Menu", command=self.app.admin_dashboard.show_admin_interface).pack(pady=20)

    def show_check_out_process(self, reservation_id, room_number, room_id):
        self.app.window_manager.clear_container()
        frame = ctk.CTkScrollableFrame(self.app.container, corner_radius=8)
        frame.pack(pady=20, padx=20, expand=True, fill="both")
        ctk.CTkLabel(frame, text=f"Check-out: Res #{reservation_id}", font=("Helvetica", 22, "bold")).pack(pady=10)
        
        res = query("SELECT * FROM reservation WHERE reservation_id=?", (reservation_id,), fetchone=True)
        cust = query("SELECT * FROM customer WHERE customer_id=?", (res['customer_id'],), fetchone=True)
        CustomerModel.calculate_and_create_bill(reservation_id)
        bill = query("SELECT * FROM billing WHERE reservation_id=?", (reservation_id,), fetchone=True)
        services = query("SELECT s.service_name, rs.quantity, rs.service_price FROM reservation_services rs JOIN service s ON rs.service_id = s.service_id WHERE rs.reservation_id = ?", (reservation_id,), fetchall=True)

        # Info
        info_frame = ctk.CTkFrame(frame)
        info_frame.pack(fill='x', padx=10, pady=5)
        ctk.CTkLabel(info_frame, text="Details", font=("Arial", 14, "bold")).pack(anchor='w', padx=10, pady=5)
        
        # --- NEW: Added Cashier Name Display ---
        cashier = bill['cashier_name'] if bill and bill['cashier_name'] else "Admin Cashier"
        guest_txt = (f"Customer: {cust['full_name']}\nRoom: {room_number or 'None'}\n"
                     f"Processed by: {cashier}\n"  # <--- ADDED HERE
                     f"Guests: A({res['count_adults']}) K({res['count_kids']}) P({res['count_pwd']}) S({res['count_seniors']})")
        ctk.CTkLabel(info_frame, text=guest_txt, justify='left').pack(anchor='w', padx=10, pady=5)

        # Services
        svc_frame = ctk.CTkFrame(frame)
        svc_frame.pack(fill='x', padx=10, pady=5)
        ctk.CTkLabel(svc_frame, text="Services", font=("Arial", 14, "bold")).pack(anchor='w', padx=10, pady=5)
        if services:
            for s in services: ctk.CTkLabel(svc_frame, text=f"• {s['service_name']} (x{s['quantity']}) - ₱{s['service_price']:.2f}", justify='left').pack(anchor='w', padx=20, pady=2)
        else: ctk.CTkLabel(svc_frame, text="No services.").pack(anchor='w', padx=20)

        # Billing
        fin_frame = ctk.CTkFrame(frame)
        fin_frame.pack(fill='x', padx=10, pady=5)
        total = bill['service_charges'] or 0.0
        disc = bill['discount_amount'] or 0.0
        final = bill['final_amount'] or 0.0
        paid = bill['amount_paid'] or 0.0
        balance = final - paid
        
        ctk.CTkLabel(fin_frame, text="Billing", font=("Arial", 14, "bold")).pack(anchor='w', padx=10, pady=5)
        fin_txt = (f"Subtotal: ₱{total:.2f}\nDiscount: -₱{disc:.2f}\nTotal Due: ₱{final:.2f}\nPaid: ₱{paid:.2f}\n\nBALANCE: ₱{balance:.2f}")
        ctk.CTkLabel(fin_frame, text=fin_txt, justify='left', font=("Courier", 14)).pack(anchor='w', padx=20, pady=5)

        # Payment
        if balance > 0:
            pay_frame = ctk.CTkFrame(frame)
            pay_frame.pack(fill='x', padx=10, pady=10)
            ctk.CTkLabel(pay_frame, text="Settle Balance", font=("Arial", 14, "bold")).pack(pady=5)
            amount_var = tk.StringVar(value=f"{balance:.2f}")
            ctk.CTkEntry(pay_frame, textvariable=amount_var, state='readonly').pack(pady=5)
            method_var = tk.StringVar(value="Cash")
            ctk.CTkOptionMenu(pay_frame, variable=method_var, values=["Cash", "Card", "E-Wallet"]).pack(pady=5)
            
            def pay_and_checkout():
                try:
                    pay_amt = float(amount_var.get())
                    CustomerModel.record_payment(reservation_id, res['customer_id'], pay_amt, method_var.get())
                    self.finalize_checkout_logic(reservation_id, room_id, room_number)
                except Exception as e: messagebox.showerror("Error", f"Payment failed: {e}")
            ctk.CTkButton(pay_frame, text="Pay & Check-out", command=pay_and_checkout, fg_color="#27ae60").pack(pady=10)
        else:
            ctk.CTkLabel(frame, text="PAID", font=("Arial", 16, "bold"), text_color="green").pack(pady=10)
            ctk.CTkButton(frame, text="Check-out", command=lambda: self.finalize_checkout_logic(reservation_id, room_id, room_number)).pack(pady=10)
        
        ctk.CTkButton(frame, text="Back", command=self.show_check_in_list, fg_color="transparent", border_width=1).pack(pady=5)

    def finalize_checkout_logic(self, reservation_id, room_id, room_number):
        try:
            CustomerModel.checkout_reservation(reservation_id)
            msg = f"Reservation #{reservation_id} checked out."
            if room_id:
                if messagebox.askyesno("Housekeeping", f"Mark Room {room_number} for Cleaning?"):
                    RoomModel.set_room_status(room_id, 'cleaning'); msg += "\nMarked for Cleaning."
                else: RoomModel.set_room_status(room_id, 'available'); msg += "\nMarked Available."
            messagebox.showinfo("Success", msg)
            self.show_check_in_list()
        except Exception as e: messagebox.showerror("Error", f"Checkout failed: {e}")

    def show_housekeeping_list(self):
        self.app.window_manager.clear_container()
        frame = ctk.CTkScrollableFrame(self.app.container, corner_radius=8)
        frame.pack(pady=20, padx=20, expand=True, fill="both")
        ctk.CTkLabel(frame, text="Housekeeping Status", font=("Helvetica", 22)).pack(pady=10)
        rows = query("SELECT * FROM room WHERE status = 'cleaning' ORDER BY room_number", fetchall=True)
        if not rows: ctk.CTkLabel(frame, text="No rooms require cleaning.", font=("Helvetica", 16)).pack(pady=20)
        else:
            for row in rows:
                r_frame = ctk.CTkFrame(frame)
                r_frame.pack(fill='x', padx=10, pady=5)
                ctk.CTkLabel(r_frame, text=f"{row['room_number']} ({row['type']})", font=("Arial", 14, "bold")).pack(side='left', padx=20, pady=15)
                def mark_clean(rid):
                    if messagebox.askyesno("Confirm", "Mark room as clean?"): RoomModel.set_room_status(rid, 'available'); self.show_housekeeping_list()
                ctk.CTkButton(r_frame, text="Mark Clean", fg_color="green", command=lambda r=row['room_id']: mark_clean(r)).pack(side='right', padx=20)
        ctk.CTkButton(frame, text="Back", command=self.app.admin_dashboard.show_admin_interface).pack(pady=20)