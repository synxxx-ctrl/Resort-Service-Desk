import customtkinter as ctk
from tkinter import messagebox, simpledialog
from datetime import datetime
from db import query, execute
from models import MaintenanceModel, RoomModel, CustomerModel, AmenityModel

class MaintenanceController:
    def __init__(self, app):
        self.app = app

    def show_maintenance_dashboard(self):
        self.app.window_manager.clear_container()
        
        frame = ctk.CTkScrollableFrame(self.app.container, corner_radius=8)
        frame.pack(pady=20, padx=20, expand=True, fill="both")

        ctk.CTkLabel(frame, text="Service Maintenance & Guest Concerns", font=("Helvetica", 22)).pack(pady=10)

        # --- Section 1: Report New Issue ---
        ctk.CTkLabel(frame, text="Report Issue for Active Guest Services", font=("Arial", 16, "bold")).pack(pady=5, anchor="w", padx=20)
        
        active_services = query("""
            SELECT 
                r.reservation_id, 
                c.full_name, 
                c.customer_id,
                s.service_name, 
                s.service_id,
                s.stock_total,
                rs.id AS svc_link_id,
                rs.quantity,
                rm.room_id,
                rm.room_number
            FROM reservation r
            JOIN customer c ON r.customer_id = c.customer_id
            JOIN reservation_services rs ON r.reservation_id = rs.reservation_id
            JOIN service s ON rs.service_id = s.service_id
            LEFT JOIN room rm ON r.room_id = rm.room_id
            WHERE (r.status = 'Checked-in' OR r.status = 'Pending')
            ORDER BY r.reservation_id DESC
        """, fetchall=True)

        if not active_services:
            ctk.CTkLabel(frame, text="No active services found.").pack(pady=5, padx=20, anchor="w")
        else:
            for item in active_services:
                row_f = ctk.CTkFrame(frame)
                row_f.pack(fill='x', padx=20, pady=5)
                
                display_name = item['service_name']
                if "Room Fee" in display_name and item['room_number']:
                    display_name = f"Room {item['room_number']} ({display_name})"
                
                lbl = ctk.CTkLabel(row_f, text=f"{display_name} - {item['full_name']}")
                lbl.pack(side="left", padx=10)
                
                ctk.CTkButton(row_f, text="Report Issue", fg_color="#e74c3c", 
                              command=lambda i=item: self.open_report_dialog(i)).pack(side="right", padx=10)

        ctk.CTkFrame(frame, height=2, fg_color="gray").pack(fill="x", pady=20, padx=10)

        # --- Section 2: Active Maintenance ---
        ctk.CTkLabel(frame, text="Units/Services Under Maintenance", font=("Arial", 16, "bold")).pack(pady=5, anchor="w", padx=20)
        
        issues = query("""
            SELECT m.*, rm.room_number, c.full_name 
            FROM maintenance_logs m
            LEFT JOIN room rm ON m.room_id = rm.room_id
            LEFT JOIN customer c ON m.reported_by_customer_id = c.customer_id
            WHERE m.status = 'Pending'
        """, fetchall=True)

        if not issues:
            ctk.CTkLabel(frame, text="No maintenance logs.").pack(pady=5, padx=20, anchor="w")
        else:
            for issue in issues:
                i_f = ctk.CTkFrame(frame)
                i_f.pack(fill='x', padx=20, pady=5)
                
                target = f"Room {issue['room_number']}" if issue['room_number'] else "General/Amenity"
                
                details = (f"Target: {target} | Reported By: {issue['full_name']}\n"
                           f"Issue: {issue['issue_description']} | Action: {issue['action_taken']}")
                ctk.CTkLabel(i_f, text=details, justify="left").pack(side="left", padx=10, pady=5)
                
                ctk.CTkButton(i_f, text="Verify Fixed", fg_color="#27ae60", 
                              command=lambda lid=issue['log_id']: self.verify_fixed(lid)).pack(side="right", padx=10)

        ctk.CTkButton(frame, text="Back to Admin Menu", command=self.app.admin_dashboard.show_admin_interface).pack(pady=20)

    def open_report_dialog(self, item_data):
        service_name = item_data['service_name']
        issue = simpledialog.askstring("Report Issue", f"Describe issue with {service_name}:", parent=self.app)
        if not issue: return

        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Select Resolution")
        dialog.geometry("400x300")
        dialog.transient(self.app)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=f"Action for {service_name}", font=("Arial", 16)).pack(pady=15)

        def process_refund():
            # 1. Get Billing Info
            bill = query("SELECT amount_paid, compensation FROM billing WHERE reservation_id=?", (item_data['reservation_id'],), fetchone=True)
            if not bill:
                messagebox.showerror("Error", "Billing record not found.", parent=dialog)
                return

            amount_paid = bill['amount_paid'] if bill['amount_paid'] else 0.0
            current_comp = bill['compensation'] if bill['compensation'] else 0.0
            
            # Max Refund is what they actually paid out of pocket minus any previous refunds
            max_refundable = amount_paid - current_comp

            # STRICT CHECK: Must have paid something to get a refund
            if amount_paid <= 0:
                messagebox.showerror("Refund Unavailable", "Customer has NOT paid yet. Cannot process refund.\nIf you wish to cancel the charge, consider voiding the transaction instead.", parent=dialog)
                return
            
            if max_refundable <= 0:
                messagebox.showerror("Refund Unavailable", "Fully refunded already.", parent=dialog); return

            # 3. Ask for amount
            choice = messagebox.askyesno("Refund Type", f"Amount Paid: ₱{amount_paid:.2f}\n\nClick YES for FULL REMAINING REFUND (₱{max_refundable:.2f})\nClick NO for Partial Refund", parent=dialog)
            
            refund_amount = 0.0
            if choice: 
                refund_amount = max_refundable
            else:
                user_input = simpledialog.askfloat("Partial Refund", f"Enter amount (Max: ₱{max_refundable:.2f}):", parent=dialog)
                if user_input is None: return 
                if user_input <= 0:
                    messagebox.showerror("Error", "Invalid amount.", parent=dialog); return
                if user_input > max_refundable:
                    messagebox.showerror("Over-Refund Error", f"Cannot refund ₱{user_input:.2f}.\nThe customer only paid ₱{amount_paid:.2f} (Available: {max_refundable}).", parent=dialog)
                    return
                refund_amount = user_input

            # 4. Process Refund AND Deduct from Amount Paid
            execute("""
                UPDATE billing 
                SET compensation = compensation + ?, 
                    amount_paid = amount_paid - ? 
                WHERE reservation_id=?
            """, (refund_amount, refund_amount, item_data['reservation_id']))
            
            # Log Issue
            r_id = item_data['room_id'] if item_data['room_id'] else None
            MaintenanceModel.report_issue(r_id, item_data['customer_id'], f"{service_name}: {issue}", f"Refunded ₱{refund_amount}")
            
            CustomerModel.calculate_and_create_bill(item_data['reservation_id'])
            
            messagebox.showinfo("Success", f"Refund of ₱{refund_amount:.2f} processed.")
            dialog.destroy()
            self.show_maintenance_dashboard()

        def process_swap():
            is_room = "Room Fee" in service_name or "Cottage" in service_name
            
            swap_diag = ctk.CTkToplevel(self.app)
            swap_diag.title("Select Replacement")
            swap_diag.geometry("350x450")
            swap_diag.transient(dialog)
            
            # FIX: Force focus to the new window so it's clickable
            swap_diag.lift()
            swap_diag.focus_force()
            swap_diag.grab_set()
            
            sf = ctk.CTkScrollableFrame(swap_diag)
            sf.pack(fill="both", expand=True)

            if is_room:
                avail = RoomModel.get_available_rooms(datetime.now().isoformat(), datetime.now().isoformat())
                if not avail:
                    messagebox.showerror("Error", "No available units to swap to.", parent=dialog); swap_diag.destroy(); return
                
                def select_room(new_r):
                    r_id = item_data['room_id']
                    MaintenanceModel.report_issue(r_id, item_data['customer_id'], f"{service_name}: {issue}", f"Swapped to {new_r['room_number']}")
                    execute("UPDATE reservation SET room_id=? WHERE reservation_id=?", (new_r['room_id'], item_data['reservation_id']))
                    RoomModel.set_room_status(new_r['room_id'], 'occupied')
                    if r_id: RoomModel.set_room_status(r_id, 'maintenance')
                    messagebox.showinfo("Success", f"{service_name} replaced.")
                    swap_diag.destroy(); dialog.destroy(); self.show_maintenance_dashboard()

                for room in avail:
                    ctk.CTkButton(sf, text=f"{room['room_number']} ({room['room_capacity']}pax)", command=lambda r=room: select_room(r)).pack(pady=5)
            else:
                keyword = service_name.split()[0] # e.g., "Karaoke"
                # FIX: Only show other options (don't swap for the exact same broken ID if possible, though for generic amenities like 'Karaoke' the ID is same. Logic below handles stock check)
                # If amenity is generic (ID is same for all instances), we just check stock.
                replacements = query(f"SELECT * FROM service WHERE service_name LIKE ?", (f"%{keyword}%",), fetchall=True)
                
                valid_options = []
                for rep in replacements:
                    stk = AmenityModel.get_available_stock(rep['service_id'], rep['stock_total'])
                    if stk > 0:
                        valid_options.append((rep, stk))

                if not valid_options:
                    ctk.CTkLabel(sf, text=f"No available {keyword} options.").pack(pady=20)
                else:
                    def select_service(new_svc):
                        MaintenanceModel.report_issue(None, item_data['customer_id'], f"{service_name}: {issue}", f"Swapped to {new_svc['service_name']}")
                        
                        # FIX: Use direct access to avoid "Record ID missing" error
                        link_id = item_data['svc_link_id']
                        if link_id:
                            execute("UPDATE reservation_services SET service_id=?, service_price=? WHERE id=?", (new_svc['service_id'], new_svc['base_price'], link_id))
                            CustomerModel.calculate_and_create_bill(item_data['reservation_id'])
                            messagebox.showinfo("Success", f"{service_name} replaced.")
                            swap_diag.destroy(); dialog.destroy(); self.show_maintenance_dashboard()
                        else: messagebox.showerror("Error", "Record ID missing.")

                    for svc, stock in valid_options:
                        ctk.CTkButton(sf, text=f"{svc['service_name']} (Avail: {stock})", command=lambda s=svc: select_service(s)).pack(pady=5)

        ctk.CTkButton(dialog, text="Refund / Compensation", command=process_refund, fg_color="#e67e22").pack(pady=10)
        ctk.CTkButton(dialog, text="Swap Service / Unit", command=process_swap, fg_color="#3498db").pack(pady=10)
        ctk.CTkButton(dialog, text="Cancel", command=dialog.destroy, fg_color="gray").pack(pady=10)

    def verify_fixed(self, log_id):
        if messagebox.askyesno("Confirm", "Is this verified fixed?"):
            MaintenanceModel.resolve_issue(log_id)
            self.show_maintenance_dashboard()