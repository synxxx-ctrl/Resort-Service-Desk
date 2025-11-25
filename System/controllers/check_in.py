import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from db import query, execute
from models import CustomerModel, RoomModel # ADDED RoomModel

class CheckInOutController:
    def __init__(self, app):
        """
        Initialize the CheckInOutController.
        :param app: Reference to the main application class.
        """
        self.app = app

    def show_check_in_list(self):
        self.app.window_manager.clear_container()
        
        frame = ctk.CTkScrollableFrame(self.app.container, corner_radius=8)
        frame.pack(pady=20, padx=20, expand=True, fill="both")

        ctk.CTkLabel(frame, text="Currently Checked-in Guests", font=("Helvetica", 22)).pack(pady=10)
        
        # Correct query using billing fields (since they now exist after schema update)
        rows = query("""
            SELECT 
                r.reservation_id,
                r.check_in_date,
                r.check_out_date,
                r.num_guests,
                r.status,
                r.room_id,
                c.full_name, 
                c.username AS customer_code, 
                rm.room_number,
                b.final_amount,
                b.amount_paid
            FROM reservation r
            JOIN customer c ON r.customer_id = c.customer_id
            LEFT JOIN room rm ON r.room_id = rm.room_id
            LEFT JOIN billing b ON r.reservation_id = b.reservation_id
            WHERE r.status = 'Checked-in'
            ORDER BY r.check_in_date DESC
        """, fetchall=True)

        if not rows:
            ctk.CTkLabel(frame, text="No guests are currently checked-in.", font=("Helvetica", 16)).pack(pady=20)
        else:
            for row in rows:
                res_frame = ctk.CTkFrame(frame, corner_radius=6)
                res_frame.pack(fill='x', padx=10, pady=5)
                
                # Calculate balance using fields from billing table
                final_amount = row['final_amount'] if row['final_amount'] is not None else 0
                amount_paid = row['amount_paid'] if row['amount_paid'] is not None else 0
                balance_due = final_amount - amount_paid

                info = (
                    f"ID: {row['reservation_id']} | Room: {row['room_number'] if row['room_number'] else 'N/A'} | Guests: {row['num_guests']}\n"
                    f"Customer: {row['full_name']} (Code: {row['customer_code']})\n"
                    f"Dates: {row['check_in_date']} to {row['check_out_date']} (Expected)\n"
                    f"Status: {row['status']} | Final Amount: ₱{final_amount:.2f}\n"
                    f"Paid: ₱{amount_paid:.2f} | Balance Due: ₱{balance_due:.2f}"
                )
                
                ctk.CTkLabel(res_frame, text=info, justify='left').pack(side='left', padx=10, pady=10, anchor='w')
                
                # Check-out button for this specific reservation
                ctk.CTkButton(
                    res_frame, 
                    text="Check-out & Bill",
                    command=lambda res_id=row['reservation_id'], room_num=row['room_number'], r_id=row['room_id']: 
                        self.show_check_out_process(res_id, room_num, r_id)
                ).pack(side='right', padx=10, pady=10)

        # --- BACK BUTTON ---
        ctk.CTkButton(frame, text="Back to Admin Menu", command=self.app.admin_dashboard.show_admin_interface).pack(pady=20)


    def show_check_out_process(self, reservation_id, room_number, room_id):
        self.app.window_manager.clear_container()
        
        frame = ctk.CTkScrollableFrame(self.app.container, corner_radius=8)
        frame.pack(pady=20, padx=20, expand=True, fill="both")

        ctk.CTkLabel(frame, text=f"Check-out: Reservation #{reservation_id} (Room {room_number if room_number else 'N/A'})", font=("Helvetica", 22)).pack(pady=10)
        
        reservation = query("SELECT r.*, c.full_name, c.customer_id FROM reservation r JOIN customer c ON r.customer_id = c.customer_id WHERE r.reservation_id = ?", (reservation_id,), fetchone=True)
        
        if not reservation:
            messagebox.showerror("Error", "Reservation not found.")
            self.show_check_in_list()
            return
        
        # 1. Billing Summary
        # Ensure a billing record exists and is up-to-date (updates final_amount based on services)
        CustomerModel.calculate_and_create_bill(reservation_id)
        billing = query("SELECT * FROM billing WHERE reservation_id = ?", (reservation_id,), fetchone=True)
        
        # FIX: Ensure billing exists
        if not billing:
             messagebox.showerror("Error", "Billing record not found for this reservation.")
             self.show_check_in_list()
             return

        # Calculate Final Amount Due
        final_amount = billing['final_amount'] if billing['final_amount'] is not None else 0.0
        amount_paid = billing['amount_paid'] if billing['amount_paid'] is not None else 0.0

        balance_due = final_amount - amount_paid

        # Display Billing Info
        bill_frame = ctk.CTkFrame(frame, fg_color='transparent')
        bill_frame.pack(fill='x', pady=10)
        ctk.CTkLabel(bill_frame, text="Billing Summary", font=("Helvetica", 18)).pack(pady=5)
        ctk.CTkLabel(bill_frame, text=f"Total Charges: ₱{final_amount:.2f}").pack(pady=2)
        ctk.CTkLabel(bill_frame, text=f"Amount Paid (Deposits/Initial): ₱{amount_paid:.2f}").pack(pady=2)
        
        balance_label = ctk.CTkLabel(bill_frame, text=f"BALANCE DUE: ₱{balance_due:.2f}", font=("Helvetica", 18), text_color='red' if balance_due > 0 else 'green')
        balance_label.pack(pady=5)

        # 2. Payment Section
        ctk.CTkFrame(frame, height=2, corner_radius=0, fg_color='gray').pack(fill='x', padx=5, pady=15)
        ctk.CTkLabel(frame, text="Process Final Payment", font=("Helvetica", 18)).pack(pady=5)

        # FIX: Ensure we use balance_due for initial amount
        amount_var = tk.StringVar(value=f"{balance_due:.2f}" if balance_due > 0 else "0.00")
        payment_methods = ['Cash', 'Credit Card', 'Bank Transfer', 'E-Wallet', 'No Payment Due']
        method_var = tk.StringVar(value='No Payment Due' if balance_due <= 0 else payment_methods[0])
        
        ctk.CTkLabel(frame, text="Payment Amount:").pack(pady=2)
        # FIX: Use 'readonly' state for 0 balance, but allow 'normal' for balance > 0
        amount_entry = ctk.CTkEntry(frame, textvariable=amount_var, state='readonly' if balance_due <= 0 else 'normal')
        amount_entry.pack(pady=2)

        ctk.CTkLabel(frame, text="Payment Method:").pack(pady=2)
        method_menu = ctk.CTkOptionMenu(frame, variable=method_var, values=payment_methods)
        method_menu.pack(pady=2)

        def finalize_checkout():
            try:
                pay_amount = float(amount_var.get())
            except ValueError:
                messagebox.showerror("Error", "Invalid payment amount.")
                return
            
            method = method_var.get()
            
            # Balance validation
            if balance_due > 0 and pay_amount < balance_due and method != 'No Payment Due':
                messagebox.showerror("Error", f"Payment amount (₱{pay_amount:.2f}) is less than the balance due (₱{balance_due:.2f}).")
                return
            
            if pay_amount < 0:
                messagebox.showerror("Error", "Payment amount cannot be negative.")
                return

            try:
                # 1. Record the payment if amount > 0
                if pay_amount > 0 and method != 'No Payment Due':
                    CustomerModel.record_payment(reservation_id, reservation['customer_id'], pay_amount, method)
                
                # 2. Finalize Check-out in the database
                CustomerModel.checkout_reservation(reservation_id)
                
                # 3. Mark room as available (Only if room_id exists)
                if room_id:
                    RoomModel.set_room_status(room_id, 'available')
                
                messagebox.showinfo("Success", f"Reservation #{reservation_id} checked out successfully. Room {room_number if room_number else 'N/A'} is now available.")
                self.show_check_in_list() # Return to the check-in list
                
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to finalize check-out: {e}")
                
        # Checkout button command
        checkout_btn = ctk.CTkButton(frame, text="FINALIZE CHECK-OUT", command=finalize_checkout)
        checkout_btn.pack(pady=20)
        
        # Back button for the checkout process screen
        ctk.CTkButton(frame, text="Back to Check-in List", command=self.show_check_in_list).pack(pady=10)