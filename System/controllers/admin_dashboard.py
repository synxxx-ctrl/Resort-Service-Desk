import customtkinter as ctk
from tkinter import messagebox

class AdminDashboard:
    def __init__(self, app):
        """
        Initialize the AdminDashboard.
        :param app: Reference to the main application class.
        """
        self.app = app

    def show_admin_interface(self):
        """
        Displays the main Admin Dashboard with buttons to manage the system.
        """
        # --- FIX: START ---
        # 1. Clear the WHOLE window (removes Registration form or old menus)
        for widget in self.app.winfo_children():
            widget.destroy()

        # 2. Re-create the main container
        # We must do this because customer_register (in some flows) might have destroyed the previous one
        self.app.container = ctk.CTkFrame(self.app)
        self.app.container.pack(fill="both", expand=True)
        # --- FIX: END ---

        # 3. Create the inner frame for the menu
        frame = ctk.CTkFrame(self.app.container)
        frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="Admin Dashboard", font=("Helvetica", 30)).pack(pady=20)

        # ------------------- Reporting & Management -------------------
        ctk.CTkLabel(frame, text="Reporting & System Management", font=("Helvetica", 16)).pack(pady=10)
        
        # Note: Assuming reservation_controller handles viewing all reservations
        # If 'show_reservations' is not in reservation_controller yet, you will need to add it there.
        ctk.CTkButton(
            frame, 
            text="View Reservations", 
            command=lambda: self.app.reservation_controller.show_reservations() if hasattr(self.app.reservation_controller, 'show_reservations') else print("Error: show_reservations not found")
        ).pack(pady=6)
        
        # Route to TransactionController
        ctk.CTkButton(
            frame, 
            text="View Transactions", 
            command=self.app.transaction_controller.show_transactions
        ).pack(pady=6)
        
        # Route to CheckInOutController
        ctk.CTkButton(
            frame, 
            text="View Checked-in Guests", 
            command=self.app.check_in_controller.show_check_in_list
        ).pack(pady=6)
        
        # Route to ReportController
        ctk.CTkButton(
            frame, 
            text="Generate Report", 
            command=self.app.report_controller.generate_report
        ).pack(pady=6)
        
        # Route to AuthController
        ctk.CTkButton(
            frame, 
            text="Change Admin Credentials", 
            command=self.app.auth_controller.change_admin_credentials
        ).pack(pady=6)
        
        ctk.CTkFrame(frame, height=2, fg_color="gray35").pack(fill="x", pady=15)

        # ------------------- Customer Management (NEW) -------------------
        ctk.CTkLabel(frame, text="Customer Management", font=("Helvetica", 16)).pack(pady=10)
        
        # Route to CustomerController
        ctk.CTkButton(
            frame, 
            text="Customer Lookup (Name Search)", 
            command=self.app.customer_controller.customer_lookup_admin
        ).pack(pady=8)
        
        ctk.CTkButton(
            frame, 
            text="New Customer / Register", 
            command=self.app.customer_controller.customer_register
        ).pack(pady=8)

        # ------------------- Back Button -------------------
        # Route to AuthController
        ctk.CTkButton(
            frame, 
            text="Back", 
            command=self.app.auth_controller.logout_admin
        ).pack()


    def show_admin_customer_dashboard(self):
        """
        Displays a dashboard for the Admin to perform actions ON BEHALF of a specific customer.
        """
        if not hasattr(self.app, 'current_customer') or not self.app.current_customer:
            messagebox.showerror("Error", "No customer loaded.")
            return
        
        # Use WindowManager to clear container
        self.app.window_manager.clear_container()
        
        frame = ctk.CTkScrollableFrame(self.app.container)
        frame.pack(pady=12, padx=12, expand=True, fill="both")
        
        cust_name = self.app.current_customer['full_name']
        cust_user = self.app.current_customer['username']
        
        ctk.CTkLabel(frame, text=f"Servicing Customer: {cust_name} (ID: {cust_user})", font=("Helvetica", 22)).pack(pady=8)
        
        # Route to ReservationController
        ctk.CTkButton(
            frame, 
            text="Make a Reservation", 
            width=240, 
            command=self.app.reservation_controller.show_make_reservation
        ).pack(pady=8)
        
        # Route to ReservationController (as per your list #5)
        ctk.CTkButton(
            frame, 
            text="Check-in Right Now (No dates)", 
            width=240, 
            command=self.app.reservation_controller.check_in_now
        ).pack(pady=8)
        
        # Route to CustomerController
        ctk.CTkButton(
            frame, 
            text="View Customer Info", 
            width=240, 
            command=self.app.customer_controller.show_current_customer_info
        ).pack(pady=8)
        
        # Route to PaymentController
        ctk.CTkButton(
            frame, 
            text="Process Payment", 
            width=240, 
            command=self.app.payment_controller.show_make_payment
        ).pack(pady=8)
        
        ctk.CTkButton(
            frame, 
            text="View Receipts", 
            width=240, 
            command=self.app.payment_controller.show_receipts
        ).pack(pady=8)

        # Return to the main admin interface (Calling method within this class)
        ctk.CTkButton(
            frame, 
            text="Back to Admin Menu", 
            width=240, 
            command=self.show_admin_interface
        ).pack(pady=16)