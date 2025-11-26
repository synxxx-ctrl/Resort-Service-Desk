import customtkinter as ctk
from tkinter import messagebox

class AdminDashboard:
    def __init__(self, app):
        self.app = app

    def show_admin_interface(self):
        # --- FIX: Resize window to a larger dashboard size ---
        self.app.geometry("1024x720") 
        self.app.resizable(True, True)
        # 1. Clear window
        for widget in self.app.winfo_children():
            widget.destroy()
        # 2. Re-create container
        self.app.container = ctk.CTkFrame(self.app)
        self.app.container.pack(fill="both", expand=True)

        # 3. Menu Frame
        frame = ctk.CTkFrame(self.app.container)
        frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="Admin Dashboard", font=("Helvetica", 30)).pack(pady=20)

        # Reporting & Management
        ctk.CTkLabel(frame, text="Reporting & System Management", font=("Helvetica", 16)).pack(pady=10)
        
        ctk.CTkButton(frame, text="View Reservations", command=lambda: self.app.reservation_controller.show_reservations()).pack(pady=6)
        ctk.CTkButton(frame, text="View Transactions", command=self.app.transaction_controller.show_transactions).pack(pady=6)
        ctk.CTkButton(frame, text="View Checked-in Guests / Check-out", command=self.app.check_in_controller.show_check_in_list).pack(pady=6)
        ctk.CTkButton(frame, text="Housekeeping Status", command=self.app.check_in_controller.show_housekeeping_list, fg_color="#e67e22", hover_color="#d35400").pack(pady=6)
        
        # Maintenance Button
        ctk.CTkButton(frame, text="Service Maintenance & Concerns", command=self.app.maintenance_controller.show_maintenance_dashboard, fg_color="#c0392b", hover_color="#e74c3c").pack(pady=6)
        
        ctk.CTkButton(frame, text="Generate Report", command=self.app.report_controller.generate_report).pack(pady=6)
        ctk.CTkButton(frame, text="Change Admin Credentials", command=self.app.auth_controller.change_admin_credentials).pack(pady=6)
        
        ctk.CTkFrame(frame, height=2, fg_color="gray35").pack(fill="x", pady=15)

        # Customer Management
        ctk.CTkLabel(frame, text="Customer Management", font=("Helvetica", 16)).pack(pady=10)
        ctk.CTkButton(frame, text="Customer Lookup (Name Search)", command=self.app.customer_controller.customer_lookup_admin).pack(pady=8)
        ctk.CTkButton(frame, text="New Customer / Register", command=self.app.customer_controller.customer_register).pack(pady=8)

        # Logout
        ctk.CTkButton(frame, text="Logout", command=self.app.auth_controller.logout_admin, fg_color="#ff0000", hover_color="#eb1010").pack(pady=20)

    def show_admin_customer_dashboard(self):
        if not hasattr(self.app, 'current_customer') or not self.app.current_customer:
            messagebox.showerror("Error", "No customer loaded.")
            return
        # Ensure window is large if accessing from other contexts
        self.app.geometry("1024x720")
        self.app.window_manager.clear_container()
        frame = ctk.CTkScrollableFrame(self.app.container)
        frame.pack(pady=12, padx=12, expand=True, fill="both")
        
        cust_name = self.app.current_customer['full_name']
        cust_user = self.app.current_customer['username']
        
        ctk.CTkLabel(frame, text=f"Servicing Customer: {cust_name} (ID: {cust_user})", font=("Helvetica", 22)).pack(pady=8)
        
        ctk.CTkButton(frame, text="Make a Reservation / Check-In", width=240, command=self.app.reservation_controller.show_make_reservation).pack(pady=8)
        ctk.CTkButton(frame, text="View Customer Info", width=240, command=self.app.customer_controller.show_current_customer_info).pack(pady=8)
        ctk.CTkButton(frame, text="Back to Admin Menu", width=240, command=self.show_admin_interface).pack(pady=16)