import customtkinter as ctk
from tkinter import messagebox

class AdminDashboard:
    def __init__(self, app):
        self.app = app

    def show_admin_interface(self):
        # Resize window
        self.app.geometry("1024x720") 
        self.app.resizable(True, True)
        
        # --- FIX: Completely destroy the old container to remove the "Empty Space" ---
        # If we just 'clear' it, the empty frame stays packed and takes up space.
        if hasattr(self.app, 'container') and self.app.container is not None:
            self.app.container.destroy()

        # 2. Re-create container
        self.app.container = ctk.CTkFrame(self.app)
        self.app.container.pack(fill="both", expand=True)

        # 3. Menu Frame (Scrollable)
        frame = ctk.CTkScrollableFrame(self.app.container) 
        frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="Admin Dashboard", font=("Helvetica", 30, "bold")).pack(pady=20)

        # --- UNIFIED BUTTON STYLE ---
        btn_style = {
            "width": 350,
            "height": 45,
            "font": ("Helvetica", 14),
            "fg_color": "#2c3e50",  # Unified Color (Dark Blue-Grey)
            "hover_color": "#34495e"
        }

        # --- SECTIONS ---
        
        # 1. Front Desk
        ctk.CTkLabel(frame, text="Front Desk & Operations", font=("Helvetica", 18, "bold")).pack(pady=(10, 5))
        
        ctk.CTkButton(frame, text="View All Reservations", command=lambda: self.app.reservation_controller.show_reservations(), **btn_style).pack(pady=5)
        ctk.CTkButton(frame, text="Check-in / Check-out Guests", command=self.app.check_in_controller.show_check_in_list, **btn_style).pack(pady=5)
        ctk.CTkButton(frame, text="Housekeeping Status", command=self.app.check_in_controller.show_housekeeping_list, **btn_style).pack(pady=5)
        ctk.CTkButton(frame, text="Transaction History", command=self.app.transaction_controller.show_transactions, **btn_style).pack(pady=5)
        
        # 2. Services
        ctk.CTkLabel(frame, text="Services & Maintenance", font=("Helvetica", 18, "bold")).pack(pady=(20, 5))
        ctk.CTkButton(frame, text="Service Maintenance & Concerns", command=self.app.maintenance_controller.show_maintenance_dashboard, **btn_style).pack(pady=5)
        
        # 3. System
        ctk.CTkLabel(frame, text="System & Reports", font=("Helvetica", 18, "bold")).pack(pady=(20, 5))
        ctk.CTkButton(frame, text="Generate Reports", command=self.app.report_controller.generate_report, **btn_style).pack(pady=5)
        ctk.CTkButton(frame, text="Change Admin Credentials", command=self.app.auth_controller.change_admin_credentials, **btn_style).pack(pady=5)
        
        # Divider
        ctk.CTkFrame(frame, height=2, width=350, fg_color="gray60").pack(pady=20)

        # 4. Customer Management
        ctk.CTkLabel(frame, text="Customer Management", font=("Helvetica", 18, "bold")).pack(pady=(5, 5))
        ctk.CTkButton(frame, text="Customer Lookup", command=self.app.customer_controller.customer_lookup_admin, **btn_style).pack(pady=5)
        ctk.CTkButton(frame, text="Register New Customer", command=self.app.customer_controller.customer_register, **btn_style).pack(pady=5)

        # Logout (Unique Style - Red)
        ctk.CTkButton(frame, text="Logout", command=self.app.auth_controller.logout_admin, 
                      width=350, height=45, font=("Helvetica", 14, "bold"),
                      fg_color="#c0392b", hover_color="#e74c3c").pack(pady=30)

    def show_admin_customer_dashboard(self):
        if not hasattr(self.app, 'current_customer') or not self.app.current_customer:
            messagebox.showerror("Error", "No customer loaded.")
            return
        
        # Also clean up container here to be safe
        if hasattr(self.app, 'container') and self.app.container is not None:
            self.app.container.destroy()
            
        self.app.container = ctk.CTkFrame(self.app)
        self.app.container.pack(fill="both", expand=True)
        
        self.app.geometry("1024x720")
        
        frame = ctk.CTkScrollableFrame(self.app.container)
        frame.pack(pady=12, padx=12, expand=True, fill="both")
        
        cust_name = self.app.current_customer['full_name']
        cust_user = self.app.current_customer['username']
        
        ctk.CTkLabel(frame, text=f"Servicing Customer: {cust_name}", font=("Helvetica", 26, "bold")).pack(pady=(20, 5))
        ctk.CTkLabel(frame, text=f"(ID: {cust_user})", font=("Helvetica", 16)).pack(pady=(0, 20))
        
        # Style for customer dashboard buttons
        cust_btn_style = {
            "width": 300,
            "height": 50,
            "font": ("Helvetica", 16),
            "fg_color": "#2980b9",
            "hover_color": "#3498db"
        }
        
        ctk.CTkButton(frame, text="Make Reservation / Check-In", command=self.app.reservation_controller.show_make_reservation, **cust_btn_style).pack(pady=10)
        ctk.CTkButton(frame, text="View Customer Receipts", command=self.app.payment_controller.show_receipts, **cust_btn_style).pack(pady=10)
        ctk.CTkButton(frame, text="View Customer Info", command=self.app.customer_controller.show_current_customer_info, **cust_btn_style).pack(pady=10)
        
        ctk.CTkButton(frame, text="Back to Admin Menu", width=300, height=50, font=("Helvetica", 16), 
                      command=self.show_admin_interface, fg_color="transparent", border_width=2, text_color=("gray10", "gray90")).pack(pady=30)