import customtkinter as ctk
from admin_dashboard import AdminDashboard
from auth_controller import AuthController
from customer_controller import CustomerController
from reservation_controller import ReservationController
from transaction_controller import TransactionController
from report_controller import ReportController
from window_manager import WindowManager

class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Resort Service Desk")
        self.geometry("1100x700")

        # ---------------- State ----------------
        self.current_customer = None
        self.is_admin_mode = False
        self.cart = []
        self.open_windows = {}

        # ---------------- Controllers ----------------
        self.window_manager = WindowManager(self)
        self.auth = AuthController(self)
        self.admin_dashboard = AdminDashboard(self)
        self.customer_controller = CustomerController(self)
        self.reservation_controller = ReservationController(self)
        self.transaction_controller = TransactionController(self)
        self.report_controller = ReportController(self)  # <-- Added report controller

        # ---------------- Start App ----------------
        self.show_main_menu()

    # ---------------- Main Menu ----------------
    def show_main_menu(self):
        self.clear_container()
        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True)
        self.container = container

        ctk.CTkLabel(container, text="Welcome to the Main Menu", font=("Helvetica", 30)).pack(pady=50)
        ctk.CTkButton(container, text="Admin Login", command=self.auth.open_admin_login).pack(pady=10)
        ctk.CTkButton(container, text="Exit", command=self.quit).pack(pady=10)
        self.is_admin_mode = False

    # ---------------- Utility ----------------
    def clear_container(self):
        if hasattr(self, 'container') and self.container.winfo_exists():
            for widget in self.container.winfo_children():
                widget.destroy()


if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
