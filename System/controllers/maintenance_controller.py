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
        ctk.CTkLabel(frame, text="Report Issue for Active Guest Services", font=("Arial", 16, "bold")).pack(pady=5, anchor="w", padx=20)
        
        active_services = query("""
            SELECT r.reservation_id, c.full_name, c.customer_id, s.service_name, s.service_id, s.stock_total, rs.id AS svc_link_id, rs.quantity, rm.room_id, rm.room_number
            FROM reservation r
            JOIN customer c ON r.customer_id = c.customer_id
            JOIN reservation_services rs ON r.reservation_id = rs.reservation_id
            JOIN service s ON rs.service_id = s.service_id
            LEFT JOIN room rm ON r.room_id = rm.room_id
            WHERE (r.status = 'Checked-in' OR r.status = 'Pending')
            ORDER BY r.reservation_id DESC
        """, fetchall=True)

        if not active_services: ctk.CTkLabel(frame, text="No active services found.").pack(pady=5, padx=20, anchor="w")
        else:
            for item in active_services:
                row_f = ctk.CTkFrame(frame)
                row_f.pack(fill='x', padx=20, pady=5)
                display_name = f"Room {item['room_number']} ({item['service_name']})" if "Room Fee" in item['service_name'] and item['room_number'] else item['service_name']
                ctk.CTkLabel(row_f, text=f"{display_name} - {item['full_name']}").pack(side="left", padx=10)
                ctk.CTkButton(row_f, text="Report Issue", fg_color="#e74c3c", command=lambda i=item: self.open_report_dialog(i)).pack(side="right", padx=10)

        ctk.CTkFrame(frame, height=2, fg_color="gray").pack(fill="x", pady=20, padx=10)
        ctk.CTkLabel(frame, text="Units/Services Under Maintenance", font=("Arial", 16, "bold")).pack(pady=5, anchor="w", padx=20)
        
        issues = query("""SELECT m.*, rm.room_number, c.full_name FROM maintenance_logs m LEFT JOIN room rm ON m.room_id = rm.room_id LEFT JOIN customer c ON m.reported_by_customer_id = c.customer_id WHERE m.status = 'Pending'""", fetchall=True)
        if not issues: ctk.CTkLabel(frame, text="No maintenance logs.").pack(pady=5, padx=20, anchor="w")
        else:
            for issue in issues:
                i_f = ctk.CTkFrame(frame)
                i_f.pack(fill='x', padx=20, pady=5)
                target = f"Room {issue['room_number']}" if issue['room_number'] else "Amenity"
                ctk.CTkLabel(i_f, text=f"Target: {target} | {issue['issue_description']} | {issue['action_taken']}").pack(side="left", padx=10)
                ctk.CTkButton(i_f, text="Verify Fixed", fg_color="#27ae60", command=lambda lid=issue['log_id']: self.verify_fixed(lid)).pack(side="right", padx=10)
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
            bill = query("SELECT amount_paid, compensation FROM billing WHERE reservation_id=?", (item_data['reservation_id'],), fetchone=True)
            if not bill: messagebox.showerror("Error", "Billing not found.", parent=dialog); return
            paid, comp = bill['amount_paid'] or 0.0, bill['compensation'] or 0.0
            max_ref = paid - comp
            if paid <= 0 or max_ref <= 0: messagebox.showerror("Error", "Refund unavailable.", parent=dialog); return
            
            choice = messagebox.askyesno("Refund", f"Max: ₱{max_ref:.2f}\nYES=Full, NO=Partial", parent=dialog)
            amt = max_ref if choice else simpledialog.askfloat("Partial", f"Enter amount (Max: ₱{max_ref:.2f})", parent=dialog)
            if amt is None or amt <= 0 or amt > max_ref: messagebox.showerror("Error", "Invalid amount.", parent=dialog); return
            
            execute("UPDATE billing SET compensation = compensation + ? WHERE reservation_id=?", (amt, item_data['reservation_id']))
            r_id = item_data['room_id'] if item_data['room_id'] else None
            MaintenanceModel.report_issue(r_id, item_data['customer_id'], f"{service_name}: {issue}", f"Refunded ₱{amt}")
            CustomerModel.calculate_and_create_bill(item_data['reservation_id'])
            messagebox.showinfo("Success", "Refund applied."); dialog.destroy(); self.show_maintenance_dashboard()

        def process_swap():
            is_room = "Room Fee" in service_name or "Cottage" in service_name
            swap_diag = ctk.CTkToplevel(self.app)
            swap_diag.title("Select Replacement")
            swap_diag.geometry("350x450")
            swap_diag.transient(dialog)
            sf = ctk.CTkScrollableFrame(swap_diag)
            sf.pack(fill="both", expand=True)

            if is_room:
                avail = RoomModel.get_available_rooms(datetime.now().isoformat(), datetime.now().isoformat())
                if not avail: messagebox.showerror("Error", "No rooms available.", parent=dialog); swap_diag.destroy(); return
                def sel_r(new_r):
                    MaintenanceModel.report_issue(item_data['room_id'], item_data['customer_id'], f"{service_name}: {issue}", f"Swapped to {new_r['room_number']}")
                    execute("UPDATE reservation SET room_id=? WHERE reservation_id=?", (new_r['room_id'], item_data['reservation_id']))
                    RoomModel.set_room_status(new_r['room_id'], 'occupied')
                    messagebox.showinfo("Success", "Swapped."); swap_diag.destroy(); dialog.destroy(); self.show_maintenance_dashboard()
                for r in avail: ctk.CTkButton(sf, text=f"{r['room_number']} ({r['room_capacity']}pax)", command=lambda x=r: sel_r(x)).pack(pady=5)
            else:
                # FILTER BY CATEGORY & CHECK STOCK
                keyword = service_name.split()[0]
                reps = query(f"SELECT * FROM service WHERE service_name LIKE ? AND service_id != ?", (f"%{keyword}%", item_data['service_id']), fetchall=True)
                valid = []
                for r in reps:
                    stk = AmenityModel.get_available_stock(r['service_id'], r['stock_total'])
                    if stk > 0: valid.append((r, stk))
                
                if not valid: ctk.CTkLabel(sf, text=f"No {keyword} replacements available.").pack(pady=20)
                else:
                    def sel_s(new_s):
                        MaintenanceModel.report_issue(None, item_data['customer_id'], f"{service_name}: {issue}", f"Swapped to {new_s['service_name']}")
                        execute("UPDATE reservation_services SET service_id=?, service_price=? WHERE id=?", (new_s['service_id'], new_s['base_price'], item_data['svc_link_id']))
                        CustomerModel.calculate_and_create_bill(item_data['reservation_id'])
                        messagebox.showinfo("Success", "Swapped."); swap_diag.destroy(); dialog.destroy(); self.show_maintenance_dashboard()
                    for s, k in valid: ctk.CTkButton(sf, text=f"{s['service_name']} (Avail: {k})", command=lambda x=s: sel_s(x)).pack(pady=5)

        ctk.CTkButton(dialog, text="Refund / Compensation", command=process_refund, fg_color="#e67e22").pack(pady=10)
        ctk.CTkButton(dialog, text="Swap Service / Unit", command=process_swap, fg_color="#3498db").pack(pady=10)
        ctk.CTkButton(dialog, text="Cancel", command=dialog.destroy, fg_color="gray").pack(pady=10)

    def verify_fixed(self, log_id):
        if messagebox.askyesno("Confirm", "Is this verified fixed?"):
            MaintenanceModel.resolve_issue(log_id)
            self.show_maintenance_dashboard()