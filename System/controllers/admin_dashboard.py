import customtkinter as ctk
from tkinter import messagebox

class AdminDashboard:
    def __init__(self, app):
        self.app = app
        self.sidebar_frame = None

    def show_admin_interface(self):
        # 1. Setup Main Window Geometry
        self.app.geometry("1300x800")
        self.app.title("Resort Service Desk - Admin")
        self.app.resizable(True, True)

        # 2. CLEAR EVERYTHING from the root window first
        for widget in self.app.winfo_children():
            if isinstance(widget, ctk.CTkToplevel): continue 
            widget.destroy()

        # 3. Create the Main Grid Layout (2 Columns)
        self.app.grid_columnconfigure(0, weight=0) 
        self.app.grid_columnconfigure(1, weight=1)
        self.app.grid_rowconfigure(0, weight=1)

        # --- LEFT: SIDEBAR FRAME ---
        self.sidebar_frame = ctk.CTkFrame(self.app, width=250, corner_radius=0, fg_color="#2b2b2b")
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False) # Force fixed width

        # --- RIGHT: CONTENT CONTAINER ---
        content_area = ctk.CTkFrame(self.app, corner_radius=0, fg_color="transparent")
        content_area.grid(row=0, column=1, sticky="nsew")
        
        # KEY STEP: Redirect the app's main container reference
        self.app.container = content_area

        # 4. Render Sidebar Buttons
        self._setup_sidebar_buttons()

        # 5. Show Default View
        self.show_default_view()

    def _setup_sidebar_buttons(self):
        """Helper to create the unified sidebar buttons"""
        
        # --- 1. LOGOUT BUTTON (Pinned to Bottom) ---
        ctk.CTkButton(self.sidebar_frame, text="  🚪  Logout", 
                      command=self.app.auth_controller.logout_admin, 
                      width=220, height=40, font=("Arial", 13, "bold"),
                      fg_color="#c0392b", hover_color="#e74c3c", anchor="center").pack(side="bottom", pady=20, padx=10)

        # --- 2. HEADER ---
        ctk.CTkLabel(self.sidebar_frame, text="Admin Dashboard", font=("Helvetica", 20, "bold"), text_color="white").pack(side="top", pady=(30, 20))

        # Button Style
        btn_style = {
            "width": 220,
            "height": 40,
            "font": ("Arial", 13, "bold"),
            "fg_color": "transparent",
            "text_color": ("gray90", "gray90"),
            "hover_color": ("gray40", "gray40"),
            "anchor": "w"
        }

        # --- SECTION: OPERATIONS ---
        ctk.CTkLabel(self.sidebar_frame, text="FRONT DESK", font=("Arial", 12, "bold"), text_color="gray60", anchor="w").pack(side="top", fill="x", padx=20, pady=(20,5))
        
        ctk.CTkButton(self.sidebar_frame, text="  📅  Reservations", command=self.app.reservation_controller.show_reservations, **btn_style).pack(side="top", pady=2, padx=10)
        ctk.CTkButton(self.sidebar_frame, text="  🔑  Check-in / Out", command=self.app.check_in_controller.show_check_in_list, **btn_style).pack(side="top", pady=2, padx=10)
        ctk.CTkButton(self.sidebar_frame, text="  🧹  Housekeeping", command=self.app.check_in_controller.show_housekeeping_list, **btn_style).pack(side="top", pady=2, padx=10)
        ctk.CTkButton(self.sidebar_frame, text="  💳  Transactions", command=self.app.transaction_controller.show_transactions, **btn_style).pack(side="top", pady=2, padx=10)

        # --- SECTION: SERVICES ---
        ctk.CTkLabel(self.sidebar_frame, text="SERVICES", font=("Arial", 12, "bold"), text_color="gray60", anchor="w").pack(side="top", fill="x", padx=20, pady=(20,5))
        
        ctk.CTkButton(self.sidebar_frame, text="  🛠️  Maintenance", command=self.app.maintenance_controller.show_maintenance_dashboard, **btn_style).pack(side="top", pady=2, padx=10)

        # --- SECTION: ADMIN ---
        ctk.CTkLabel(self.sidebar_frame, text="SYSTEM", font=("Arial", 12, "bold"), text_color="gray60", anchor="w").pack(side="top", fill="x", padx=20, pady=(20,5))
        
        ctk.CTkButton(self.sidebar_frame, text="  📊  Reports", command=self.app.report_controller.generate_report, **btn_style).pack(side="top", pady=2, padx=10)
        ctk.CTkButton(self.sidebar_frame, text="  🔒  Credentials", command=self.app.auth_controller.change_admin_credentials, **btn_style).pack(side="top", pady=2, padx=10)

        # --- SECTION: CUSTOMERS ---
        # UPDATED LABEL HERE:
        ctk.CTkLabel(self.sidebar_frame, text="CUSTOMER MANAGEMENT", font=("Arial", 12, "bold"), text_color="gray60", anchor="w").pack(side="top", fill="x", padx=20, pady=(20,5))
        
        ctk.CTkButton(self.sidebar_frame, text="  🔍  Lookup Customer", command=self.app.customer_controller.customer_lookup_admin, **btn_style).pack(side="top", pady=2, padx=10)
        ctk.CTkButton(self.sidebar_frame, text="  ➕  New Register", command=self.app.customer_controller.customer_register, **btn_style).pack(side="top", pady=2, padx=10)

    def show_default_view(self):
        """Shows the big Bituin Sands logo when no option is selected."""
        self.app.window_manager.clear_container()
        frame = ctk.CTkFrame(self.app.container, fg_color="transparent")
        frame.pack(expand=True, fill="both")
        ctk.CTkLabel(frame, text="Bituin Sands", font=("Times New Roman", 60, "bold"), text_color=("gray30", "gray80")).pack(expand=True, anchor="center")
        ctk.CTkLabel(frame, text="Resort Service Desk System", font=("Arial", 20), text_color="gray").place(relx=0.5, rely=0.55, anchor="center")
    
    def show_admin_customer_dashboard(self):
        """Displays the 'Service Customer' menu in the main content area."""
        if not hasattr(self.app, 'current_customer') or not self.app.current_customer:
            messagebox.showerror("Error", "No customer loaded.")
            return

        self.app.window_manager.clear_container()
        
        # Center Frame
        frame = ctk.CTkFrame(self.app.container, fg_color="transparent")
        frame.pack(expand=True, fill="both", padx=40, pady=40)

        cust = self.app.current_customer
        
        # Header Info
        ctk.CTkLabel(frame, text=f"Servicing: {cust['full_name']}", font=("Arial", 32, "bold"), text_color="#3498db").pack(pady=(10, 5))
        ctk.CTkLabel(frame, text=f"Customer ID: {cust['username']}", font=("Arial", 16), text_color="gray").pack(pady=(0, 40))

        # Buttons Setup
        btn_style = {
            "width": 400,
            "height": 60,
            "font": ("Arial", 18, "bold"),
            "corner_radius": 10
        }

        # 1. Make Reservation
        ctk.CTkButton(frame, text="📅   Create New Reservation / Check-In", 
                      command=self.app.reservation_controller.show_make_reservation, 
                      fg_color="#27ae60", hover_color="#2ecc71", **btn_style).pack(pady=10)

        # 2. View Receipts
        ctk.CTkButton(frame, text="📜   View Transaction History", 
                      command=self.app.payment_controller.show_receipts, 
                      fg_color="#2980b9", hover_color="#3498db", **btn_style).pack(pady=10)

        # 3. View Profile
        ctk.CTkButton(frame, text="👤   View Customer Details", 
                      command=self.app.customer_controller.show_current_customer_info, 
                      fg_color="#8e44ad", hover_color="#9b59b6", **btn_style).pack(pady=10)

        # 4. DELETE CUSTOMER (New Button)
        ctk.CTkButton(frame, text="🗑️   Delete Customer", 
                      command=self.app.customer_controller.delete_current_customer, 
                      fg_color="#c0392b", hover_color="#e74c3c", **btn_style).pack(pady=10)

        # Close Session
        ctk.CTkFrame(frame, height=2, width=300, fg_color="gray60").pack(pady=30)
        
        def close_session():
            self.app.current_customer = None
            self.show_default_view()

        ctk.CTkButton(frame, text="Close Customer Session", command=close_session, 
                      fg_color="transparent", border_width=1, text_color="gray", width=200).pack(pady=10)