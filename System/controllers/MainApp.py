import customtkinter as ctk

# --- Import all your controllers ---
from auth_controller import AuthController
from window_manager import WindowManager
from admin_dashboard import AdminDashboard
from customer_controller import CustomerController
from reservation_controller import ReservationController
from check_in import CheckInOutController       # Was missing in your snippet
from payment_controller import PaymentController # Was missing in your snippet
from report_controller import ReportController
from transaction_controller import TransactionController

class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # 1. Basic Window Setup
        self.title("Resort Service Desk")
        self.geometry("1100x700")

        # 2. Shared State Variables
        # These are accessed by controllers using self.app.variable_name
        self.current_customer = None
        self.is_admin_mode = False
        self.cart = []
        self.open_windows = {}
        self.container = None  # Will be created by WindowManager

        # 3. Initialize Controllers
        # We pass 'self' so controllers can access the app and other controllers
        self.window_manager = WindowManager(self)
        self.auth_controller = AuthController(self)
        self.admin_dashboard = AdminDashboard(self)
        self.customer_controller = CustomerController(self)
        self.reservation_controller = ReservationController(self)
        self.check_in_controller = CheckInOutController(self)
        self.payment_controller = PaymentController(self)
        self.report_controller = ReportController(self)
        self.transaction_controller = TransactionController(self)

        # 4. Start the Application Flow
        # We delegate the UI creation to the WindowManager
        self.window_manager.show_main_menu()

if __name__ == "__main__":
    # Optional: Set theme
    ctk.set_appearance_mode("System") 
    ctk.set_default_color_theme("blue")
    
    app = MainApp()
    app.mainloop()