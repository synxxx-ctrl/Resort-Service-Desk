import customtkinter as ctk
from tkinter import messagebox, simpledialog
import re
from db import get_conn, query
from models import CustomerModel
from utils import is_valid_email, is_valid_phone, generate_unique_customer_code # IMPORTED UTILS FUNCTIONS

class CustomerController:
    def __init__(self, app):
        """
        Initialize the CustomerController.
        :param app: Reference to the main application class.
        """
        self.app = app

    def customer_register(self):
        # --- FIX 1: Use window_manager to clear.
        self.app.window_manager.clear_container()
        
        # 1. UI Setup
        # NOTE: All widgets must be parented to self.app.container
        ctk.CTkLabel(self.app.container, text="Customer Registration", font=("Arial", 24, "bold")).pack(pady=30)

        # Form Frame
        form_frame = ctk.CTkFrame(self.app.container)
        form_frame.pack(pady=20, padx=20)

        # Name
        ctk.CTkLabel(form_frame, text="Full Name:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        entry_name = ctk.CTkEntry(form_frame, width=250, placeholder_text="Enter full name")
        entry_name.grid(row=0, column=1, padx=10, pady=10)

        # Email
        ctk.CTkLabel(form_frame, text="Email:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        entry_email = ctk.CTkEntry(form_frame, width=250, placeholder_text="Enter email address")
        entry_email.grid(row=1, column=1, padx=10, pady=10)

        # Contact
        ctk.CTkLabel(form_frame, text="Contact Number:").grid(row=2, column=0, padx=10, pady=10, sticky="e")
        entry_contact = ctk.CTkEntry(form_frame, width=250, placeholder_text="Enter phone number")
        entry_contact.grid(row=2, column=1, padx=10, pady=10)

        # 2. Submit Logic 
        def submit_form():
            name = entry_name.get().strip()
            email = entry_email.get().strip()
            contact = entry_contact.get().strip()

            # Basic Validation
            if not name or not email or not contact:
                messagebox.showerror("Error", "All fields are required.")
                return

            if not is_valid_email(email):
                messagebox.showerror("Invalid Email", "Please enter a valid email address.")
                return
            
            if not is_valid_phone(contact):
                messagebox.showerror("Invalid Number", "Please enter a valid phone number.")
                return

            # Database Insert
            try:
                # --- FIX: Generate unique customer code (username) ---
                customer_code = generate_unique_customer_code()
                
                conn = get_conn()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO customer (username, full_name, email, contact_number) VALUES (?, ?, ?, ?)",
                    (customer_code, name, email, contact) # ADDED customer_code
                )
                customer_id = cur.lastrowid
                conn.commit()
                conn.close()

                # Set current customer in the MAIN APP state
                self.app.current_customer = CustomerModel.get_customer_by_id(customer_id)
                self.app.cart = []

                # Go to Admin Customer Dashboard
                # Ensure AdminDashboard is initialized in main app as self.app.admin_dashboard
                self.app.admin_dashboard.show_admin_customer_dashboard()

            except Exception as e:
                messagebox.showerror("Database Error", f"An error occurred: {e}")

        # 3. Buttons
        # NOTE: Attached to self.app.container
        btn_submit = ctk.CTkButton(self.app.container, text="Register & Continue", command=submit_form, fg_color="green")
        btn_submit.pack(pady=20)

        # Back Button
        # NOTE: Routes back to Admin Interface
        btn_back = ctk.CTkButton(
            self.app.container, 
            text="Cancel", 
            command=self.app.admin_dashboard.show_admin_interface, 
            fg_color="transparent", 
            border_width=1
        )
        btn_back.pack(pady=5)

    def customer_lookup_admin(self):
        # Dialog parent is self.app
        name = simpledialog.askstring("Customer Lookup", "Enter customer name or code:", parent=self.app)
        if not name:
            return
        
        # Search by full_name or username (customer code)
        row = query("SELECT * FROM customer WHERE full_name LIKE ? OR username = ? LIMIT 1", ('%' + name + '%', name), fetchone=True)
        
        if not row:
            messagebox.showerror("Not Found", "No customer found with that name or code.")
            return
        
        # Update Main App State
        self.app.current_customer = row
        self.app.cart = []
        
        # Route to Dashboard
        self.app.admin_dashboard.show_admin_customer_dashboard()

    def show_current_customer_info(self):
        if not hasattr(self.app, 'current_customer') or not self.app.current_customer:
            messagebox.showerror("Error", "No customer loaded.")
            return
        
        info = (
            f"Code: {self.app.current_customer['username']}\n"
            f"Name: {self.app.current_customer['full_name']}\n"
            f"Email: {self.app.current_customer['email']}\n"
            f"Contact: {self.app.current_customer['contact_number']}"
        )
        
        # Use WindowManager to show text
        self.app.window_manager.open_text_window("Customer Info", info)