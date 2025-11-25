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
from models import CustomerModel # IMPORTED CustomerModel

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
        
    # --- CUSTOMER DASHBOARD ROUTING METHODS (Missing in original) ---
    def show_customer_reservations(self):
        self.window_manager.clear_container()
        frame = ctk.CTkScrollableFrame(self.container)
        frame.pack(pady=12, padx=12, expand=True, fill="both")
        
        ctk.CTkLabel(frame, text="My Reservations", font=("Helvetica", 22)).pack(pady=8)
        
        # Fetch data (using the model query for history, though more direct query might be simpler)
        summary = CustomerModel.get_customer_summary(self.current_customer['customer_id'])
        
        reservations = {}
        for item in summary['services_history']:
            res_id = item['reservation_id']
            if res_id not in reservations:
                reservations[res_id] = {
                    'check_in': item['check_in_date'],
                    'check_out': item['check_out_date'],
                    'guests': item['num_guests'],
                    'status': item['status'],
                    'services': []
                }
            if item['service_name']:
                reservations[res_id]['services'].append(f"{item['service_name']} x{item['quantity']}")
        
        if not reservations:
            ctk.CTkLabel(frame, text="No reservations found.").pack(pady=10)
        else:
            for res_id, res in reservations.items():
                res_frame = ctk.CTkFrame(frame)
                res_frame.pack(fill='x', pady=4, padx=6)
                
                info = (f"Reservation ID: {res_id} | Status: {res['status']}\n"
                        f"Dates: {res['check_in']} to {res['check_out']} | Guests: {res['guests']}\n"
                        f"Services: {', '.join(res['services']) if res['services'] else 'None'}")
                ctk.CTkLabel(res_frame, text=info, justify='left').pack(anchor='w', padx=6, pady=4)
                
        ctk.CTkButton(frame, text="Back to Dashboard", command=self.window_manager.show_customer_dashboard).pack(pady=12)

    def show_customer_services(self):
        self.window_manager.clear_container()
        frame = ctk.CTkScrollableFrame(self.container)
        frame.pack(pady=12, padx=12, expand=True, fill="both")
        
        ctk.CTkLabel(frame, text="Services & Billing Status", font=("Helvetica", 22)).pack(pady=8)

        # We'll use the existing show_make_payment screen as a good proxy for billing status, 
        # but modify it to be read-only for customer view if required.
        # For simplicity and to reuse PaymentController logic:
        self.payment_controller.show_make_payment()
        # NOTE: The current show_make_payment is Admin-focused (has a Pay button). 
        # A proper customer view would require a separate, read-only method in PaymentController.
        # Sticking to the Admin flow for now, but adding a note.
        ctk.CTkLabel(frame, text="*** NOTE: This is the payment screen, which shows outstanding bills. ***", text_color='orange').pack(pady=8)


if __name__ == "__main__":
    # Optional: Set theme
    ctk.set_appearance_mode("System") 
    ctk.set_default_color_theme("blue")
    
    app = MainApp()
    app.mainloop()