import customtkinter as ctk
from models import CustomerModel

class WindowManager:
    def __init__(self, app):
        self.app = app

    def show_main_menu(self):
        self.app.auth_controller.open_admin_login()

    def show_customer_dashboard(self):
        self.clear_container()
        if not hasattr(self.app, 'current_customer') or not self.app.current_customer:
            self.show_main_menu()
            return

        frame = ctk.CTkFrame(self.app.container, corner_radius=8)
        frame.pack(pady=20, padx=20, expand=True, fill="both")

        ctk.CTkLabel(frame, text=f"Welcome, {self.app.current_customer['full_name']}!", font=("Helvetica", 24)).pack(pady=10)
        
        # REMOVED View Payments/Receipts
        ctk.CTkButton(frame, text="View Reservations", command=self.app.show_customer_reservations).pack(pady=10)
        ctk.CTkButton(frame, text="View Services History", command=self.app.show_customer_services).pack(pady=10)
        
        if hasattr(self.app, 'is_admin_mode') and self.app.is_admin_mode:
            ctk.CTkButton(frame, text="Back", command=self.app.admin_dashboard.show_admin_customer_dashboard).pack(pady=30)
        else:
            ctk.CTkButton(frame, text="Logout", command=self.show_main_menu).pack(pady=30)

    def clear_container(self):
        if hasattr(self.app, 'container') and self.app.container:
            for widget in self.app.container.winfo_children(): widget.destroy()

    def focus_or_create_window(self, key, create_fn):
        if not hasattr(self.app, 'open_windows'): self.app.open_windows = {}
        if key in self.app.open_windows and self.app.open_windows[key].winfo_exists():
            self.app.open_windows[key].focus()
            return
        w = create_fn()
        self.app.open_windows[key] = w
        w.protocol("WM_DELETE_WINDOW", lambda: (self.app.open_windows.pop(key, None), w.destroy()))
        return w

    def open_text_window(self, title, content):
        def create():
            w = ctk.CTkToplevel(self.app)
            w.title(title)
            w.geometry("800x550")
            f = ctk.CTkScrollableFrame(w, width=760, height=520)
            f.pack(padx=12, pady=12, fill='both', expand=True)
            ctk.CTkLabel(f, text=content, justify='left').pack(anchor='w')
            return w
        self.focus_or_create_window(title, create)