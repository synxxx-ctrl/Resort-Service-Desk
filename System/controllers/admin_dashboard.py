import customtkinter as ctk

class AdminDashboard:
    def __init__(self, app):
        self.app = app

    def show_admin_interface(self):
        # Clear main window
        for widget in self.app.winfo_children():
            widget.destroy()
        self.app.container = ctk.CTkFrame(self.app)
        self.app.container.pack(fill="both", expand=True)

        frame = ctk.CTkFrame(self.app.container)
        frame.pack(expand=True, fill="both", padx=20, pady=20)

        ctk.CTkLabel(frame, text="Admin Dashboard", font=("Helvetica", 30)).pack(pady=20)

        # ------------------- Reporting & System Management -------------------
        ctk.CTkLabel(frame, text="Reporting & System Management", font=("Helvetica", 16)).pack(pady=10)
        ctk.CTkButton(frame, text="View Reservations", 
                      command=self.app.reservation_controller.show_make_reservation).pack(pady=6)
        ctk.CTkButton(frame, text="View Transactions", 
                      command=self.app.transaction_controller.show_make_payment).pack(pady=6)
        ctk.CTkButton(frame, text="Generate Report",
                      command=self.app.report_controller.generate_report).pack(pady=6)
        ctk.CTkButton(frame, text="Change Admin Credentials",
                      command=self.app.auth.change_admin_credentials).pack(pady=6)

        # Separator
        ctk.CTkFrame(frame, height=2, fg_color="gray35").pack(fill="x", pady=15)

        # ------------------- Customer Management -------------------
        ctk.CTkLabel(frame, text="Customer Management", font=("Helvetica", 16)).pack(pady=10)
        ctk.CTkButton(frame, text="Customer Lookup (Name Search)", 
                      command=self.app.customer_controller.customer_lookup_admin).pack(pady=8)
        ctk.CTkButton(frame, text="New Customer / Register", 
                      command=self.app.customer_controller.customer_register).pack(pady=8)

        # ------------------- Back Button -------------------
        ctk.CTkButton(frame, text="Back", command=self.app.auth.logout_admin).pack(pady=10)
