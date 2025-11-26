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
        
        # ACTIVE SERVICES QUERY
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
                rs.service_price,
                rm.room_id,
                rm.room_number
            FROM reservation r
            JOIN customer c ON r.customer_id = c.customer_id
            JOIN reservation_services rs ON r.reservation_id = rs.reservation_id
            JOIN service s ON rs.service_id = s.service_id
            LEFT JOIN room rm ON r.room_id = rm.room_id
            WHERE (r.status = 'Checked-in' OR r.status = 'Pending')
            ORDER BY r.reservation_id DESC, rs.id ASC
        """, fetchall=True)

        # Count existing pending reports to filter list
        maintenance_counts = query("""
            SELECT reservation_id, service_id, COUNT(*) as cnt
            FROM maintenance_logs
            WHERE status = 'Pending' AND reservation_id IS NOT NULL
            GROUP BY reservation_id, service_id
        """, fetchall=True)
        
        broken_map = {}
        if maintenance_counts:
            for row in maintenance_counts:
                broken_map[(row['reservation_id'], row['service_id'])] = row['cnt']

        if not active_services:
            ctk.CTkLabel(frame, text="No active services found.").pack(pady=5, padx=20, anchor="w")
        else:
            service_total_qtys = {}
            for item in active_services:
                key = (item['reservation_id'], item['service_id'])
                service_total_qtys[key] = service_total_qtys.get(key, 0) + item['quantity']
            
            service_displayed_counter = {}

            for item in active_services:
                qty = item['quantity']
                res_id = item['reservation_id']
                svc_id = item['service_id']
                svc_name = item['service_name']
                
                key = (res_id, svc_id)
                total_qty = service_total_qtys.get(key, 0)
                broken_qty = broken_map.get(key, 0)
                
                # Show only items that are not already reported
                active_qty = max(0, total_qty - broken_qty)
                
                for _ in range(qty):
                    current_idx = service_displayed_counter.get(key, 0) + 1
                    service_displayed_counter[key] = current_idx
                    
                    if current_idx <= active_qty:
                        row_f = ctk.CTkFrame(frame)
                        row_f.pack(fill='x', padx=20, pady=5)
                        
                        display_name = svc_name
                        if "Room Fee" in display_name and item['room_number']:
                            display_name = f"Room {item['room_number']} ({display_name})"
                        else:
                            if total_qty > 1:
                                display_name = f"{display_name} #{current_idx}"

                        lbl = ctk.CTkLabel(row_f, text=f"{display_name} - {item['full_name']}")
                        lbl.pack(side="left", padx=10)
                        
                        ctk.CTkButton(row_f, text="Report Issue", fg_color="#e74c3c", 
                                      command=lambda d=item: self.open_report_dialog(d, fixed_qty=1)).pack(side="right", padx=10)

        ctk.CTkFrame(frame, height=2, fg_color="gray").pack(fill="x", pady=20, padx=10)

        # --- Section 2: Active Maintenance ---
        ctk.CTkLabel(frame, text="Units/Services Under Maintenance", font=("Arial", 16, "bold")).pack(pady=5, anchor="w", padx=20)
        
        issues = query("""
            SELECT m.*, rm.room_number, c.full_name, s.service_name
            FROM maintenance_logs m
            LEFT JOIN room rm ON m.room_id = rm.room_id
            LEFT JOIN service s ON m.service_id = s.service_id
            LEFT JOIN customer c ON m.reported_by_customer_id = c.customer_id
            WHERE m.status = 'Pending'
        """, fetchall=True)

        if not issues:
            ctk.CTkLabel(frame, text="No maintenance logs.").pack(pady=5, padx=20, anchor="w")
        else:
            for issue in issues:
                i_f = ctk.CTkFrame(frame)
                i_f.pack(fill='x', padx=20, pady=5)
                
                if issue['room_number']: target = f"Room {issue['room_number']}"
                elif issue['service_name']: target = f"{issue['service_name']} (Amenity)"
                else: target = "General/Unknown"
                
                details = (f"Target: {target} | Reported By: {issue['full_name']}\n"
                           f"Issue: {issue['issue_description']} | Action: {issue['action_taken']}")
                ctk.CTkLabel(i_f, text=details, justify="left").pack(side="left", padx=10, pady=5)
                
                ctk.CTkButton(i_f, text="Verify Fixed", fg_color="#27ae60", 
                              command=lambda lid=issue['log_id']: self.verify_fixed(lid)).pack(side="right", padx=10)

        ctk.CTkButton(frame, text="Back to Admin Menu", command=self.app.admin_dashboard.show_admin_interface).pack(pady=20)

    def open_report_dialog(self, item_data, fixed_qty=1):
        service_name = item_data['service_name']
        issue = simpledialog.askstring("Report Issue", f"Describe issue with {service_name}:", parent=self.app)
        if not issue: return

        # Use self.app as parent for transient dialogs to avoid path errors
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Select Resolution")
        dialog.geometry("400x300")
        dialog.transient(self.app)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=f"Action for {service_name}", font=("Arial", 16)).pack(pady=15)

        def process_refund():
            try:
                # 1. Validation & Data Fetching
                bill = query("SELECT amount_paid FROM billing WHERE reservation_id=?", (item_data['reservation_id'],), fetchone=True)
                if not bill:
                    messagebox.showerror("Error", "Billing record not found.", parent=self.app); return

                amount_paid = bill['amount_paid'] or 0.0
                total_refundable = amount_paid

                if total_refundable <= 0:
                    messagebox.showerror("Refund Unavailable", "No funds remaining (Fully Refunded or Unpaid).", parent=self.app); return

                # Calculate max refund for this SPECIFIC item (Price * Qty selected)
                item_price_limit = item_data['service_price'] * fixed_qty
                max_refund = min(total_refundable, item_price_limit)

                # 2. ASK: Full or Partial?
                choice = messagebox.askyesno("Refund Type", 
                    f"Processing Return for: {service_name}\n\n"
                    f"Max Refundable: ₱{max_refund:.2f}\n\n"
                    f"YES = FULL REFUND (₱{max_refund:.2f})\n"
                    f"NO = PARTIAL REFUND", parent=self.app)
                
                refund_amount = 0.0
                if choice:
                    refund_amount = max_refund
                else:
                    refund_amount = simpledialog.askfloat("Partial Refund", f"Enter Amount (Max: ₱{max_refund:.2f}):", parent=self.app)

                # 3. Input Validation
                if refund_amount is None: return # User cancelled
                if refund_amount <= 0:
                    messagebox.showerror("Error", "Invalid amount. Must be greater than 0.", parent=self.app); return
                if refund_amount > total_refundable:
                    messagebox.showerror("Error", f"Cannot refund ₱{refund_amount:.2f}. Only ₱{total_refundable:.2f} available.", parent=self.app); return

                # 4. Process DB Updates
                # Update Billing: Return Money
                execute("UPDATE billing SET amount_paid = amount_paid - ? WHERE reservation_id=?", 
                        (refund_amount, item_data['reservation_id']))
                
                # Remove Item from Reservation (Return Logic)
                link_id = item_data['svc_link_id']
                current_qty = item_data['quantity']
                
                if link_id:
                    if fixed_qty < current_qty:
                         execute("UPDATE reservation_services SET quantity = quantity - ? WHERE id=?", (fixed_qty, link_id))
                    else:
                         execute("DELETE FROM reservation_services WHERE id=?", (link_id,))

                # Log Issue (Res ID = None -> Item is now Broken Stock/Returned)
                r_id = item_data['room_id'] if item_data['room_id'] else None
                MaintenanceModel.report_issue(r_id, item_data['service_id'], None, item_data['customer_id'], 
                                              f"{service_name}: {issue}", f"Returned & Refunded ₱{refund_amount}")

                CustomerModel.calculate_and_create_bill(item_data['reservation_id'])
                messagebox.showinfo("Success", f"Refund of ₱{refund_amount:.2f} processed and item returned.", parent=self.app)
                dialog.destroy(); self.show_maintenance_dashboard()

            except Exception as e:
                messagebox.showerror("System Error", f"An error occurred during refund:\n{e}", parent=self.app)

        def process_swap():
            try:
                is_room = "Room Fee" in service_name or "Cottage" in service_name
                qty_to_swap = fixed_qty

                swap_diag = ctk.CTkToplevel(self.app)
                swap_diag.title("Select Replacement")
                swap_diag.geometry("350x450")
                swap_diag.transient(dialog)
                swap_diag.lift(); swap_diag.focus_force(); swap_diag.grab_set()
                
                sf = ctk.CTkScrollableFrame(swap_diag)
                sf.pack(fill="both", expand=True)

                if is_room:
                    avail = RoomModel.get_available_rooms(datetime.now().isoformat(), datetime.now().isoformat())
                    if not avail:
                        messagebox.showerror("Error", "No available units.", parent=self.app); swap_diag.destroy(); return
                    
                    def select_room(new_r):
                        r_id = item_data['room_id']
                        MaintenanceModel.report_issue(r_id, None, None, item_data['customer_id'], 
                                                      f"{service_name}: {issue}", f"Swapped to {new_r['room_number']}")
                        execute("UPDATE reservation SET room_id=? WHERE reservation_id=?", (new_r['room_id'], item_data['reservation_id']))
                        RoomModel.set_room_status(new_r['room_id'], 'occupied')
                        if r_id: RoomModel.set_room_status(r_id, 'maintenance')
                        messagebox.showinfo("Success", f"{service_name} replaced.", parent=self.app); swap_diag.destroy(); dialog.destroy(); self.show_maintenance_dashboard()

                    for room in avail:
                        ctk.CTkButton(sf, text=f"{room['room_number']} ({room['room_capacity']}pax)", command=lambda r=room: select_room(r)).pack(pady=5)
                else:
                    keyword = service_name.split()[0]
                    replacements = query(f"SELECT * FROM service WHERE service_name LIKE ?", (f"%{keyword}%",), fetchall=True)
                    
                    valid_options = []
                    for rep in replacements:
                        stk = AmenityModel.get_available_stock(rep['service_id'], rep['stock_total'])
                        if stk > 0: valid_options.append((rep, stk))

                    if not valid_options: ctk.CTkLabel(sf, text=f"No available {keyword} options.").pack(pady=20)
                    else:
                        def select_service(new_svc):
                            MaintenanceModel.report_issue(None, item_data['service_id'], None, item_data['customer_id'], 
                                                          f"{service_name}: {issue}", f"Swapped to {new_svc['service_name']}")
                            
                            link_id = item_data['svc_link_id']
                            current_db_qty = item_data['quantity']
                            
                            if link_id:
                                if qty_to_swap < current_db_qty:
                                    execute("UPDATE reservation_services SET quantity = quantity - ? WHERE id=?", (qty_to_swap, link_id))
                                    execute("INSERT INTO reservation_services (reservation_id, service_id, quantity, service_price) VALUES (?, ?, ?, ?)",
                                            (item_data['reservation_id'], new_svc['service_id'], qty_to_swap, new_svc['base_price']))
                                else:
                                    execute("UPDATE reservation_services SET service_id=?, service_price=? WHERE id=?", (new_svc['service_id'], new_svc['base_price'], link_id))
                                
                                CustomerModel.calculate_and_create_bill(item_data['reservation_id'])
                                messagebox.showinfo("Success", f"Replaced item.", parent=self.app); swap_diag.destroy(); dialog.destroy(); self.show_maintenance_dashboard()
                            else: messagebox.showerror("Error", "Record ID missing.", parent=self.app)

                        for svc, stock in valid_options:
                            ctk.CTkButton(sf, text=f"{svc['service_name']} (Avail: {stock})", command=lambda s=svc: select_service(s)).pack(pady=5)
            except Exception as e:
                messagebox.showerror("System Error", f"An error occurred during swap:\n{e}", parent=self.app)

        ctk.CTkButton(dialog, text="Refund / Return", command=process_refund, fg_color="#e67e22").pack(pady=10)
        ctk.CTkButton(dialog, text="Swap Service / Unit", command=process_swap, fg_color="#3498db").pack(pady=10)
        ctk.CTkButton(dialog, text="Cancel", command=dialog.destroy, fg_color="gray").pack(pady=10)

    def verify_fixed(self, log_id):
        if messagebox.askyesno("Confirm", "Is this verified fixed?", parent=self.app):
            MaintenanceModel.resolve_issue(log_id)
            self.show_maintenance_dashboard()