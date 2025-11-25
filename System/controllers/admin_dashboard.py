import customtkinter as ctk
from tkinter import messagebox

class AdminDashboard:
    def __init__(self, app):
        self.app = app

    def show_admin_interface(self):
        for widget in self.app.winfo_children(): widget.destroy()
        self.app.container = ctk.CTkFrame(self.app)
        self.app.container.pack(fill="both", expand=True)

        frame = ctk.CTkFrame(self.app.container)
        frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="Admin Dashboard", font=("Helvetica", 30)).pack(pady=20)
        
        ctk.CTkLabel(frame, text="Management", font=("Helvetica", 16)).pack(pady=10)
        ctk.CTkButton(frame, text="View Reservations", command=lambda: self.app.reservation_controller.show_reservations()).pack(pady=6)
        ctk.CTkButton(frame, text="View Transactions", command=self.app.transaction_controller.show_transactions).pack(pady=6)
        
        # The main Check-out access point
        ctk.CTkButton(frame, text="View Checked-in Guests / Check-out", command=self.app.check_in_controller.show_check_in_list).pack(pady=6)
        
        ctk.CTkButton(frame, text="Housekeeping Status", command=self.app.check_in_controller.show_housekeeping_list, fg_color="#e67e22", hover_color="#d35400").pack(pady=6)
        ctk.CTkButton(frame, text="Generate Report", command=self.app.report_controller.generate_report).pack(pady=6)
        ctk.CTkButton(frame, text="Change Admin Credentials", command=self.app.auth_controller.change_admin_credentials).pack(pady=6)
        
        ctk.CTkFrame(frame, height=2, fg_color="gray35").pack(fill="x", pady=15)
        
        ctk.CTkLabel(frame, text="Customer", font=("Helvetica", 16)).pack(pady=10)
        ctk.CTkButton(frame, text="Customer Lookup", command=self.app.customer_controller.customer_lookup_admin).pack(pady=8)
        ctk.CTkButton(frame, text="New Customer", command=self.app.customer_controller.customer_register).pack(pady=8)
        
        ctk.CTkButton(frame, text="Logout", command=self.app.auth_controller.logout_admin, fg_color="#c0392b", hover_color="#e74c3c").pack(pady=20)

    def show_admin_customer_dashboard(self):
        if not hasattr(self.app, 'current_customer') or not self.app.current_customer:
            messagebox.showerror("Error", "No customer loaded.")
            return
        
        self.app.window_manager.clear_container()
        frame = ctk.CTkScrollableFrame(self.app.container)
        frame.pack(pady=12, padx=12, expand=True, fill="both")
        
        cust = self.app.current_customer
        ctk.CTkLabel(frame, text=f"Servicing: {cust['full_name']} (ID: {cust['username']})", font=("Helvetica", 22)).pack(pady=8)
        
        # REMOVED Payment/Receipt buttons as requested
        ctk.CTkButton(frame, text="Make a Reservation / Check-In", width=240, command=self.app.reservation_controller.show_make_reservation).pack(pady=8)
        ctk.CTkButton(frame, text="View Customer Info", width=240, command=self.app.customer_controller.show_current_customer_info).pack(pady=8)
        
        ctk.CTkButton(frame, text="Back to Admin Menu", width=240, command=self.show_admin_interface).pack(pady=16)