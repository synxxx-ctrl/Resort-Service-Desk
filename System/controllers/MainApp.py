import customtkinter as ctk
# --- Import all your controllers ---
from auth_controller import AuthController
from window_manager import WindowManager
from admin_dashboard import AdminDashboard
from customer_controller import CustomerController
from reservation_controller import ReservationController
from check_in import CheckInOutController
from payment_controller import PaymentController
from report_controller import ReportController
from transaction_controller import TransactionController
from maintenance_controller import MaintenanceController

class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # 1. Basic Window Setup
        self.title("Resort Service Desk")
        self.geometry("320x260") 

        # 2. Shared State Variables
        self.current_customer = None
        self.is_admin_mode = False
        self.cart = []
        self.open_windows = {}
        
        # 3. Create the Main Container
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)

        # 4. Initialize Controllers
        self.window_manager = WindowManager(self)
        self.auth_controller = AuthController(self)
        self.admin_dashboard = AdminDashboard(self)
        self.customer_controller = CustomerController(self)
        self.reservation_controller = ReservationController(self)
        self.check_in_controller = CheckInOutController(self)
        self.payment_controller = PaymentController(self)
        self.report_controller = ReportController(self)
        self.transaction_controller = TransactionController(self)
        self.maintenance_controller = MaintenanceController(self)

        # 5. Start the Application Flow -> DIRECT TO LOGIN
        self.auth_controller.open_admin_login()

if __name__ == "__main__":
    ctk.set_appearance_mode("System") 
    ctk.set_default_color_theme("blue")
    
    app = MainApp()
    app.mainloop()