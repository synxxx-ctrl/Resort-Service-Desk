import customtkinter as ctk
from models import CustomerModel

class WindowManager:
    def __init__(self, app):
        """
        Initialize the WindowManager.
        :param app: Reference to the main application class.
        """
        self.app = app

    def show_main_menu(self):
        """Displays the main user-facing menu or initial screen."""
        self.app.geometry("1100x700")  # Set back to large size
        
        # --- SAFE SCREEN CLEARING ---
        # 1. Destroy all current widgets (including old containers)
        for widget in self.app.winfo_children():
            widget.destroy()
        
        # 2. Re-create the container so we have a place to put the new buttons
        # We attach the container to the main app instance
        self.app.container = ctk.CTkFrame(self.app)
        self.app.container.pack(fill="both", expand=True)
        # ----------------------------
        
        # Main Menu Content
        ctk.CTkLabel(self.app.container, text="Welcome to the Main Menu", font=("Helvetica", 30)).pack(pady=50)
        
        # Updated Button: "Admin Login"
        # Calls the AuthController instance located in the main app
        ctk.CTkButton(
            self.app.container, 
            text="Admin Login", 
            command=self.app.auth_controller.open_admin_login
        ).pack(pady=10)
        
        # Reset admin mode flag on the main app
        self.app.is_admin_mode = False

    def show_customer_dashboard(self):
        self.clear_container()
        
        # Access current_customer from the main app state
        if not hasattr(self.app, 'current_customer') or not self.app.current_customer:
            ctk.CTkLabel(self.app.container, text="Error: No customer selected.", font=("Helvetica", 18)).pack(pady=50)
            ctk.CTkButton(self.app.container, text="Back to Main Menu", command=self.show_main_menu).pack(pady=10)
            return

        frame = ctk.CTkFrame(self.app.container, corner_radius=8)
        frame.pack(pady=20, padx=20, expand=True, fill="both")

        # Welcome and Info
        ctk.CTkLabel(frame, text=f"Welcome, {self.app.current_customer['full_name']}!", font=("Helvetica", 24)).pack(pady=10)
        
        info_frame = ctk.CTkFrame(frame, fg_color='transparent')
        info_frame.pack(pady=10, padx=20, fill='x')

        info_text = (
            f"Customer Code: **{self.app.current_customer['username']}**\n"
            f"Email: {self.app.current_customer['email']}\n"
            f"Contact: {self.app.current_customer['contact_number']}"
        )
        ctk.CTkLabel(info_frame, text=info_text, justify='left', font=("Helvetica", 14)).pack(anchor='w', padx=10)

        # Separator
        ctk.CTkFrame(frame, height=2, corner_radius=0, fg_color='gray').pack(fill='x', padx=5, pady=20)

        # Action Buttons
        ctk.CTkLabel(frame, text="Actions", font=("Helvetica", 18)).pack(pady=10)
        
        # Links now correctly point to methods in MainApp
        ctk.CTkButton(frame, text="View Reservations", command=self.app.show_customer_reservations).pack(pady=10)
        ctk.CTkButton(frame, text="View Services and Billing", command=self.app.show_customer_services).pack(pady=10)
        ctk.CTkButton(frame, text="View Payments / Receipts", command=self.app.payment_controller.show_receipts).pack(pady=10)
        
        # Back button to Admin/Main Menu
        if hasattr(self.app, 'is_admin_mode') and self.app.is_admin_mode:
            # Calls AdminDashboard to go to Admin Customer Dashboard for continuity
            ctk.CTkButton(frame, text="Back to Admin Customer Lookup", command=self.app.admin_dashboard.show_admin_customer_dashboard).pack(pady=30)
        else:
            ctk.CTkButton(frame, text="Logout", command=self.show_main_menu).pack(pady=30)

    def clear_container(self):
        """Destroys all current widgets within the main self.app.container."""
        if hasattr(self.app, 'container') and self.app.container is not None and self.app.container.winfo_exists():
            for widget in self.app.container.winfo_children():
                widget.destroy()

    def focus_or_create_window(self, key, create_fn):
        # Initialize open_windows dict in app if not present
        if not hasattr(self.app, 'open_windows'):
            self.app.open_windows = {}

        if key in self.app.open_windows and self.app.open_windows[key].winfo_exists():
            self.app.open_windows[key].focus()
            return
        
        w = create_fn()
        self.app.open_windows[key] = w
        
        def on_close():
            if key in self.app.open_windows:
                del self.app.open_windows[key]
            w.destroy()
            
        w.protocol("WM_DELETE_WINDOW", on_close)
        return w

    def open_text_window(self, title, content):
        def create():
            w = ctk.CTkToplevel(self.app)
            w.title(title)
            w.geometry("800x550")
            frame = ctk.CTkScrollableFrame(w, width=760, height=520)
            frame.pack(padx=12, pady=12, fill='both', expand=True)
            lbl = ctk.CTkLabel(frame, text=content, justify='left')
            lbl.pack(anchor='w')
            return w
        self.focus_or_create_window(title, create)