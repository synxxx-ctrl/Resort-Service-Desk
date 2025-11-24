import customtkinter as ctk
class WindowManager:
    def __init__(self, app):
        """
        app = reference to MainApp so we can access:
        - window size
        - container
        - admin/customer flags
        - current_customer
        - other controllers
        """
        self.app = app
    # ------------------------------------------------------------
    # SHOW MAIN MENU
    # ------------------------------------------------------------
    def show_main_menu(self):
        """Displays the main user-facing menu or initial screen."""
        self.app.geometry("1100x700")

        # Destroy all widgets on screen (full reset)
        for widget in self.app.winfo_children():
            widget.destroy()

        # Recreate container frame
        self.app.container = ctk.CTkFrame(self.app)
        self.app.container.pack(fill="both", expand=True)

        # UI Elements
        ctk.CTkLabel(
            self.app.container,
            text="Welcome to the Main Menu",
            font=("Helvetica", 30)
        ).pack(pady=50)

        # Button → calls AuthController through app
        ctk.CTkButton(
            self.app.container,
            text="Admin Login",
            command=self.app.auth.open_admin_login
        ).pack(pady=10)

        # Reset admin flag
        self.app.is_admin_mode = False

    # ------------------------------------------------------------
    # SHOW CUSTOMER DASHBOARD
    # ------------------------------------------------------------
    def show_customer_dashboard(self):
        self.clear_container()

        # No customer selected → error
        if not self.app.current_customer:
            ctk.CTkLabel(
                self.app.container,
                text="Error: No customer selected.",
                font=("Helvetica", 18)
            ).pack(pady=50)

            ctk.CTkButton(
                self.app.container,
                text="Back to Main Menu",
                command=self.show_main_menu
            ).pack(pady=10)
            return

        frame = ctk.CTkFrame(self.app.container, corner_radius=8)
        frame.pack(pady=20, padx=20, expand=True, fill="both")

        # Customer Greeting
        ctk.CTkLabel(
            frame,
            text=f"Welcome, {self.app.current_customer['full_name']}!",
            font=("Helvetica", 24)
        ).pack(pady=10)

        info_frame = ctk.CTkFrame(frame, fg_color="transparent")
        info_frame.pack(pady=10, padx=20, fill='x')

        info_text = (
            f"Customer Code: **{self.app.current_customer['username']}**\n"
            f"Email: {self.app.current_customer['email']}\n"
            f"Contact: {self.app.current_customer['contact_number']}"
        )

        ctk.CTkLabel(
            info_frame,
            text=info_text,
            justify='left',
            font=("Helvetica", 14)
        ).pack(anchor='w', padx=10)

        # Separator line
        ctk.CTkFrame(
            frame,
            height=2,
            corner_radius=0,
            fg_color='gray'
        ).pack(fill='x', padx=5, pady=20)

        # Actions
        ctk.CTkLabel(frame, text="Actions", font=("Helvetica", 18)).pack(pady=10)

        ctk.CTkButton(
            frame,
            text="View Reservations",
            command=self.app.show_customer_reservations
        ).pack(pady=10)

        ctk.CTkButton(
            frame,
            text="View Services and Billing",
            command=self.app.show_customer_services
        ).pack(pady=10)

        ctk.CTkButton(
            frame,
            text="View Payments / Receipts",
            command=self.app.show_customer_transactions
        ).pack(pady=10)

        # Back behavior depends on admin mode
        if self.app.is_admin_mode:
            ctk.CTkButton(
                frame,
                text="Back to Admin Customer Lookup",
                command=self.app.customer_lookup_admin
            ).pack(pady=30)
        else:
            ctk.CTkButton(
                frame,
                text="Logout",
                command=self.show_main_menu
            ).pack(pady=30)

    # ------------------------------------------------------------
    # CLEAR CONTAINER
    # ------------------------------------------------------------
    def clear_container(self):
        """Destroys all widgets inside the screen's main container."""
        if hasattr(self.app, "container") and self.app.container.winfo_exists():
            for widget in self.app.container.winfo_children():
                widget.destroy()

    # ------------------------------------------------------------
    # WINDOW FOCUS HANDLING
    # ------------------------------------------------------------
    def focus_or_create_window(self, key, create_fn):
        """
        Ensures only ONE instance of a popup window stays open.
        """
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

    # ------------------------------------------------------------
    # OPEN TEXT WINDOW (READ-ONLY)
    # ------------------------------------------------------------
    def open_text_window(self, title, content):
        def create():
            w = ctk.CTkToplevel(self.app)
            w.title(title)
            w.geometry("800x550")

            frame = ctk.CTkScrollableFrame(w, width=760, height=520)
            frame.pack(padx=12, pady=12, fill="both", expand=True)

            ctk.CTkLabel(frame, text=content, justify="left").pack(anchor="w")
            return w

        self.focus_or_create_window(title, create)
