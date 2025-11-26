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
        
        # Main Container
        frame = ctk.CTkScrollableFrame(self.app.container, corner_radius=10)
        frame.pack(pady=15, padx=15, expand=True, fill="both")
        
        ctk.CTkLabel(frame, text="Current Guests (Checked-In)", font=("Arial", 26, "bold")).pack(pady=15)
        
        # Updated Query to get full details
        rows = query("""
            SELECT 
                r.*, 
                c.full_name, 
                c.username AS customer_code, 
                rm.room_number, 
                rm.type as room_type,
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
            ctk.CTkLabel(frame, text="No guests are currently checked-in.", font=("Arial", 16)).pack(pady=20)
        else:
            for row in rows:
                # --- GUEST CARD ---
                card = ctk.CTkFrame(frame, fg_color=("gray85", "gray25"), corner_radius=8, border_width=1, border_color="gray50")
                card.pack(fill='x', pady=8, padx=10)
                
                # Header: Room & Name
                header = ctk.CTkFrame(card, fg_color="transparent")
                header.pack(fill='x', padx=15, pady=(10,5))
                
                room_txt = f"Room {row['room_number']}" if row['room_number'] else "No Room Assigned"
                ctk.CTkLabel(header, text=f"{room_txt}", font=("Arial", 20, "bold"), text_color="#3498db").pack(side="left")
                ctk.CTkLabel(header, text=f"Res #{row['reservation_id']}", font=("Arial", 14), text_color="gray70").pack(side="right")
                
                # Separator
                ctk.CTkFrame(card, height=2, fg_color="gray60").pack(fill="x", padx=10, pady=5)
                
                # Body: Details & Finance
                body = ctk.CTkFrame(card, fg_color="transparent")
                body.pack(fill='x', padx=15, pady=5)
                
                # Left: Guest Info
                left = ctk.CTkFrame(body, fg_color="transparent")
                left.pack(side="left", fill="both", expand=True)
                
                ctk.CTkLabel(left, text=f"Guest: {row['full_name']}", font=("Arial", 16, "bold"), anchor="w").pack(fill="x")
                ctk.CTkLabel(left, text=f"Stay: {row['check_in_date']} ➔ {row['check_out_date']}", font=("Arial", 14), anchor="w").pack(fill="x")
                
                guests_txt = f"Adults: {row['count_adults']}, Kids: {row['count_kids']}, Seniors: {row['count_seniors']}"
                ctk.CTkLabel(left, text=f"Pax: {guests_txt}", font=("Arial", 13), text_color="gray80", anchor="w").pack(fill="x")

                # Right: Financials
                right = ctk.CTkFrame(body, fg_color="transparent")
                right.pack(side="right", fill="y", padx=10)
                
                final = row['final_amount'] if row['final_amount'] else 0.0
                paid = row['amount_paid'] if row['amount_paid'] else 0.0
                balance = final - paid
                
                ctk.CTkLabel(right, text=f"Total Bill: ₱{final:,.2f}", font=("Arial", 14), anchor="e").pack(fill="x")
                
                bal_color = "#e74c3c" if balance > 0 else "#27ae60" # Red if due, Green if paid
                bal_text = f"Due: ₱{balance:,.2f}" if balance > 0 else "Fully Paid"
                ctk.CTkLabel(right, text=bal_text, font=("Arial", 16, "bold"), text_color=bal_color, anchor="e").pack(fill="x")

                # Footer: Check-out Button
                btn_frame = ctk.CTkFrame(card, fg_color="transparent")
                btn_frame.pack(fill='x', padx=15, pady=(10, 15))
                
                ctk.CTkButton(btn_frame, text="Process Check-out & Billing", font=("Arial", 14, "bold"), height=35, fg_color="#c0392b", hover_color="#e74c3c",
                              command=lambda r=row: self.show_check_out_process(r['reservation_id'], r['room_number'], r['room_id'])).pack(fill="x")

        ctk.CTkButton(frame, text="Back to Dashboard", font=("Arial", 15, "bold"), height=40, command=self.app.admin_dashboard.show_admin_interface).pack(pady=20)

    def show_check_out_process(self, reservation_id, room_number, room_id):
        self.app.window_manager.clear_container()
        
        frame = ctk.CTkScrollableFrame(self.app.container, corner_radius=10)
        frame.pack(pady=15, padx=15, expand=True, fill="both")
        
        ctk.CTkLabel(frame, text=f"Check-out: Res #{reservation_id}", font=("Arial", 26, "bold")).pack(pady=10)
        
        # Refresh Data
        res = query("SELECT * FROM reservation WHERE reservation_id=?", (reservation_id,), fetchone=True)
        cust = query("SELECT * FROM customer WHERE customer_id=?", (res['customer_id'],), fetchone=True)
        
        # Ensure bill is up to date
        CustomerModel.calculate_and_create_bill(reservation_id)
        bill = query("SELECT * FROM billing WHERE reservation_id=?", (reservation_id,), fetchone=True)
        
        services = query("""
            SELECT s.service_name, rs.quantity, rs.service_price 
            FROM reservation_services rs 
            JOIN service s ON rs.service_id = s.service_id 
            WHERE rs.reservation_id = ?
        """, (reservation_id,), fetchall=True)

        # --- SECTION 1: Guest Info ---
        info_card = ctk.CTkFrame(frame, fg_color=("gray85", "gray25"))
        info_card.pack(fill='x', padx=10, pady=5)
        
        ctk.CTkLabel(info_card, text="Guest & Stay Details", font=("Arial", 16, "bold")).pack(anchor='w', padx=15, pady=(10, 5))
        
        cashier = bill['cashier_name'] if bill and bill['cashier_name'] else "Admin Cashier"
        guest_txt = (f"Customer: {cust['full_name']}\n"
                     f"Room: {room_number or 'None'}\n"
                     f"Processed by: {cashier}\n"
                     f"Guests: Adult({res['count_adults']}) Kid({res['count_kids']}) PWD({res['count_pwd']}) Senior({res['count_seniors']})")
        
        ctk.CTkLabel(info_card, text=guest_txt, justify='left', font=("Arial", 14)).pack(anchor='w', padx=15, pady=(0, 10))

        # --- SECTION 2: Bill Summary ---
        bill_card = ctk.CTkFrame(frame, fg_color=("gray85", "gray25"))
        bill_card.pack(fill='x', padx=10, pady=5)
        
        ctk.CTkLabel(bill_card, text="Final Bill Summary", font=("Arial", 16, "bold")).pack(anchor='w', padx=15, pady=(10, 5))

        total = bill['service_charges'] or 0.0
        disc = bill['discount_amount'] or 0.0
        comp = bill['compensation'] or 0.0
        final = bill['final_amount'] or 0.0
        paid = bill['amount_paid'] or 0.0
        balance = final - paid
        
        # Use a grid for cleaner numbers
        grid_f = ctk.CTkFrame(bill_card, fg_color="transparent")
        grid_f.pack(fill='x', padx=15, pady=5)
        
        ctk.CTkLabel(grid_f, text="Subtotal:", font=("Arial", 14), width=150, anchor="w").grid(row=0, column=0)
        ctk.CTkLabel(grid_f, text=f"₱{total:,.2f}", font=("Arial", 14), anchor="e").grid(row=0, column=1)
        
        if disc > 0:
            ctk.CTkLabel(grid_f, text="Discount:", font=("Arial", 14), text_color="#e67e22", width=150, anchor="w").grid(row=1, column=0)
            ctk.CTkLabel(grid_f, text=f"-₱{disc:,.2f}", font=("Arial", 14), text_color="#e67e22", anchor="e").grid(row=1, column=1)
        
        if comp > 0:
            ctk.CTkLabel(grid_f, text="Compensation:", font=("Arial", 14), text_color="#e74c3c", width=150, anchor="w").grid(row=2, column=0)
            ctk.CTkLabel(grid_f, text=f"-₱{comp:,.2f}", font=("Arial", 14), text_color="#e74c3c", anchor="e").grid(row=2, column=1)

        ctk.CTkFrame(bill_card, height=2, fg_color="gray").pack(fill='x', padx=15, pady=10) # Line
        
        ctk.CTkLabel(bill_card, text=f"TOTAL DUE: ₱{final:,.2f}", font=("Arial", 18, "bold")).pack(anchor='e', padx=20)
        ctk.CTkLabel(bill_card, text=f"Already Paid: ₱{paid:,.2f}", font=("Arial", 16)).pack(anchor='e', padx=20)
        
        bal_color = "#e74c3c" if balance > 0 else "#27ae60"
        ctk.CTkLabel(bill_card, text=f"BALANCE: ₱{balance:,.2f}", font=("Arial", 22, "bold"), text_color=bal_color).pack(anchor='e', padx=20, pady=(5, 15))

        # --- SECTION 3: Payment / Action ---
        action_card = ctk.CTkFrame(frame, fg_color="transparent")
        action_card.pack(fill='x', padx=10, pady=10)

        if balance > 0:
            ctk.CTkLabel(action_card, text="Settle Remaining Balance", font=("Arial", 16, "bold")).pack(pady=5)
            
            pay_row = ctk.CTkFrame(action_card, fg_color="transparent")
            pay_row.pack(pady=5)
            
            amount_var = tk.StringVar(value=f"{balance:.2f}")
            ctk.CTkEntry(pay_row, textvariable=amount_var, state='readonly', font=("Arial", 14), width=150).pack(side="left", padx=5)
            
            method_var = tk.StringVar(value="Cash")
            ctk.CTkOptionMenu(pay_row, variable=method_var, values=["Cash", "Card", "E-Wallet"], width=120).pack(side="left", padx=5)
            
            def pay_and_checkout():
                try:
                    pay_amt = float(amount_var.get())
                    CustomerModel.record_payment(reservation_id, res['customer_id'], pay_amt, method_var.get())
                    self.finalize_checkout_logic(reservation_id, room_id, room_number)
                except Exception as e: messagebox.showerror("Error", f"Payment failed: {e}")
            
            ctk.CTkButton(action_card, text="PAY & CHECK-OUT", font=("Arial", 16, "bold"), height=50, fg_color="#27ae60", 
                          command=pay_and_checkout).pack(fill="x", pady=10)
        else:
            ctk.CTkLabel(action_card, text="✅ BILL FULLY SETTLED", font=("Arial", 18, "bold"), text_color="#27ae60").pack(pady=10)
            ctk.CTkButton(action_card, text="COMPLETE CHECK-OUT", font=("Arial", 16, "bold"), height=50, 
                          command=lambda: self.finalize_checkout_logic(reservation_id, room_id, room_number)).pack(fill="x", pady=5)
        
        ctk.CTkButton(frame, text="Cancel / Back", command=self.show_check_in_list, fg_color="transparent", border_width=1, font=("Arial", 14)).pack(pady=5)

    def finalize_checkout_logic(self, reservation_id, room_id, room_number):
        try:
            CustomerModel.checkout_reservation(reservation_id)
            msg = f"Reservation #{reservation_id} checked out successfully."
            if room_id:
                if messagebox.askyesno("Housekeeping", f"Mark Room {room_number} for Cleaning?"):
                    RoomModel.set_room_status(room_id, 'cleaning'); msg += "\nMarked for Cleaning."
                else: RoomModel.set_room_status(room_id, 'available'); msg += "\nMarked Available."
            messagebox.showinfo("Success", msg)
            self.show_check_in_list()
        except Exception as e: messagebox.showerror("Error", f"Checkout failed: {e}")

    def show_housekeeping_list(self):
        self.app.window_manager.clear_container()
        frame = ctk.CTkScrollableFrame(self.app.container, corner_radius=10)
        frame.pack(pady=20, padx=20, expand=True, fill="both")
        
        ctk.CTkLabel(frame, text="Housekeeping Status", font=("Arial", 26, "bold")).pack(pady=10)
        
        rows = query("SELECT * FROM room WHERE status = 'cleaning' ORDER BY room_number", fetchall=True)
        
        if not rows: 
            ctk.CTkLabel(frame, text="No rooms require cleaning.", font=("Arial", 16)).pack(pady=20)
        else:
            for row in rows:
                r_frame = ctk.CTkFrame(frame, fg_color=("gray85", "gray25"))
                r_frame.pack(fill='x', padx=10, pady=5)
                
                ctk.CTkLabel(r_frame, text=f"{row['room_number']} ({row['type']})", font=("Arial", 18, "bold")).pack(side='left', padx=20, pady=15)
                
                def mark_clean(rid):
                    if messagebox.askyesno("Confirm", "Mark room as clean?"): 
                        RoomModel.set_room_status(rid, 'available')
                        self.show_housekeeping_list()
                
                ctk.CTkButton(r_frame, text="Mark Clean", font=("Arial", 14, "bold"), fg_color="green", height=40,
                              command=lambda r=row['room_id']: mark_clean(r)).pack(side='right', padx=20)
                              
        ctk.CTkButton(frame, text="Back to Dashboard", font=("Arial", 15, "bold"), height=40, command=self.app.admin_dashboard.show_admin_interface).pack(pady=20)