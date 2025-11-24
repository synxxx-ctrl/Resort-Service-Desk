# customer_controller.py

import customtkinter as ctk
from tkinter import messagebox, simpledialog
from db import get_conn, query
from models import CustomerModel
from utils import is_valid_email, is_valid_phone  # assume you have validation functions


class CustomerController:
    def __init__(self, app):
        """
        app = reference to MainApp
        """
        self.app = app

    # ------------------------------------------------------------
    # REGISTER NEW CUSTOMER
    # ------------------------------------------------------------
    def customer_register(self):
        self.app.window.clear_container()  # safe container clearing

        ctk.CTkLabel(
            self.app.container,
            text="Customer Registration",
            font=("Arial", 24, "bold")
        ).pack(pady=30)

        form_frame = ctk.CTkFrame(self.app.container)
        form_frame.pack(pady=20, padx=20)

        # Full Name
        ctk.CTkLabel(form_frame, text="Full Name:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        entry_name = ctk.CTkEntry(form_frame, width=250, placeholder_text="Enter full name")
        entry_name.grid(row=0, column=1, padx=10, pady=10)

        # Email
        ctk.CTkLabel(form_frame, text="Email:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        entry_email = ctk.CTkEntry(form_frame, width=250, placeholder_text="Enter email address")
        entry_email.grid(row=1, column=1, padx=10, pady=10)

        # Contact Number
        ctk.CTkLabel(form_frame, text="Contact Number:").grid(row=2, column=0, padx=10, pady=10, sticky="e")
        entry_contact = ctk.CTkEntry(form_frame, width=250, placeholder_text="Enter phone number")
        entry_contact.grid(row=2, column=1, padx=10, pady=10)

        # Submit Logic
        def submit_form():
            name = entry_name.get().strip()
            email = entry_email.get().strip()
            contact = entry_contact.get().strip()

            # Validation
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
                conn = get_conn()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO customer (full_name, email, contact_number) VALUES (?, ?, ?)",
                    (name, email, contact)
                )
                customer_id = cur.lastrowid
                conn.commit()
                conn.close()

                # Set current customer
                self.app.current_customer = CustomerModel.get_customer_by_id(customer_id)
                self.app.cart = []

                # Go to Admin Customer Dashboard
                self.show_admin_customer_dashboard()

            except Exception as e:
                messagebox.showerror("Database Error", f"An error occurred: {e}")

        # Buttons
        ctk.CTkButton(self.app.container, text="Register & Continue", command=submit_form, fg_color="green").pack(pady=20)
        ctk.CTkButton(self.app.container, text="Cancel", command=self.app.admin.show_admin_interface,
                      fg_color="transparent", border_width=1).pack(pady=5)

    # ------------------------------------------------------------
    # ADMIN CUSTOMER DASHBOARD
    # ------------------------------------------------------------
    def show_admin_customer_dashboard(self):
        if not self.app.current_customer:
            messagebox.showerror("Error", "No customer loaded.")
            return

        self.app.window.clear_container()

        frame = ctk.CTkScrollableFrame(self.app.container)
        frame.pack(pady=12, padx=12, expand=True, fill="both")

        ctk.CTkLabel(
            frame,
            text=f"Servicing Customer: {self.app.current_customer['full_name']} "
                 f"(ID: {self.app.current_customer['username']})",
            font=("Helvetica", 22)
        ).pack(pady=8)

        # Action Buttons
        ctk.CTkButton(frame, text="Make a Reservation", width=240, command=self.app.reservation.show_make_reservation).pack(pady=8)
        ctk.CTkButton(frame, text="Check-in Right Now (No dates)", width=240, command=self.app.reservation.check_in_now).pack(pady=8)
        ctk.CTkButton(frame, text="View Customer Info", width=240, command=self.show_current_customer_info).pack(pady=8)
        ctk.CTkButton(frame, text="Process Payment", width=240, command=self.app.payment.show_make_payment).pack(pady=8)
        ctk.CTkButton(frame, text="View Receipts", width=240, command=self.app.payment.show_receipts).pack(pady=8)

        ctk.CTkButton(frame, text="Back to Admin Menu", width=240, command=self.app.admin.show_admin_interface).pack(pady=16)

    # ------------------------------------------------------------
    # SHOW CURRENT CUSTOMER INFO
    # ------------------------------------------------------------
    def show_current_customer_info(self):
        if not self.app.current_customer:
            messagebox.showerror("Error", "No customer loaded.")
            return

        info = (
            f"Name: {self.app.current_customer['full_name']}\n"
            f"Email: {self.app.current_customer['email']}\n"
            f"Contact: {self.app.current_customer['contact_number']}"
        )
        self.app.window.open_text_window("Customer Info", info)

    # ------------------------------------------------------------
    # CUSTOMER LOOKUP FOR ADMIN
    # ------------------------------------------------------------
    def customer_lookup_admin(self):
        name = simpledialog.askstring("Customer Lookup", "Enter customer name:", parent=self.app)
        if not name:
            return

        row = query("SELECT * FROM customer WHERE full_name LIKE ? LIMIT 1", ('%' + name + '%',), fetchone=True)
        if not row:
            messagebox.showerror("Not Found", "No customer found with that name.")
            return
# customer_controller.py

import customtkinter as ctk
from tkinter import messagebox, simpledialog
from db import get_conn, query
from models import CustomerModel
from utils import is_valid_email, is_valid_phone  # assume you have validation functions


class CustomerController:
    def __init__(self, app):
        """
        app = reference to MainApp
        """
        self.app = app

    # ------------------------------------------------------------
    # REGISTER NEW CUSTOMER
    # ------------------------------------------------------------
    def customer_register(self):
        self.app.window.clear_container()  # safe container clearing

        ctk.CTkLabel(
            self.app.container,
            text="Customer Registration",
            font=("Arial", 24, "bold")
        ).pack(pady=30)

        form_frame = ctk.CTkFrame(self.app.container)
        form_frame.pack(pady=20, padx=20)

        # Full Name
        ctk.CTkLabel(form_frame, text="Full Name:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        entry_name = ctk.CTkEntry(form_frame, width=250, placeholder_text="Enter full name")
        entry_name.grid(row=0, column=1, padx=10, pady=10)

        # Email
        ctk.CTkLabel(form_frame, text="Email:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        entry_email = ctk.CTkEntry(form_frame, width=250, placeholder_text="Enter email address")
        entry_email.grid(row=1, column=1, padx=10, pady=10)

        # Contact Number
        ctk.CTkLabel(form_frame, text="Contact Number:").grid(row=2, column=0, padx=10, pady=10, sticky="e")
        entry_contact = ctk.CTkEntry(form_frame, width=250, placeholder_text="Enter phone number")
        entry_contact.grid(row=2, column=1, padx=10, pady=10)

        # Submit Logic
        def submit_form():
            name = entry_name.get().strip()
            email = entry_email.get().strip()
            contact = entry_contact.get().strip()

            # Validation
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
                conn = get_conn()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO customer (full_name, email, contact_number) VALUES (?, ?, ?)",
                    (name, email, contact)
                )
                customer_id = cur.lastrowid
                conn.commit()
                conn.close()

                # Set current customer
                self.app.current_customer = CustomerModel.get_customer_by_id(customer_id)
                self.app.cart = []

                # Go to Admin Customer Dashboard
                self.show_admin_customer_dashboard()

            except Exception as e:
                messagebox.showerror("Database Error", f"An error occurred: {e}")

        # Buttons
        ctk.CTkButton(self.app.container, text="Register & Continue", command=submit_form, fg_color="green").pack(pady=20)
        ctk.CTkButton(self.app.container, text="Cancel", command=self.app.admin.show_admin_interface,
                      fg_color="transparent", border_width=1).pack(pady=5)

    # ------------------------------------------------------------
    # ADMIN CUSTOMER DASHBOARD
    # ------------------------------------------------------------
    def show_admin_customer_dashboard(self):
        if not self.app.current_customer:
            messagebox.showerror("Error", "No customer loaded.")
            return

        self.app.window.clear_container()

        frame = ctk.CTkScrollableFrame(self.app.container)
        frame.pack(pady=12, padx=12, expand=True, fill="both")

        ctk.CTkLabel(
            frame,
            text=f"Servicing Customer: {self.app.current_customer['full_name']} "
                 f"(ID: {self.app.current_customer['username']})",
            font=("Helvetica", 22)
        ).pack(pady=8)

        # Action Buttons
        ctk.CTkButton(frame, text="Make a Reservation", width=240, command=self.app.reservation.show_make_reservation).pack(pady=8)
        ctk.CTkButton(frame, text="Check-in Right Now (No dates)", width=240, command=self.app.reservation.check_in_now).pack(pady=8)
        ctk.CTkButton(frame, text="View Customer Info", width=240, command=self.show_current_customer_info).pack(pady=8)
        ctk.CTkButton(frame, text="Process Payment", width=240, command=self.app.payment.show_make_payment).pack(pady=8)
        ctk.CTkButton(frame, text="View Receipts", width=240, command=self.app.payment.show_receipts).pack(pady=8)

        ctk.CTkButton(frame, text="Back to Admin Menu", width=240, command=self.app.admin.show_admin_interface).pack(pady=16)

    # ------------------------------------------------------------
    # SHOW CURRENT CUSTOMER INFO
    # ------------------------------------------------------------
    def show_current_customer_info(self):
        if not self.app.current_customer:
            messagebox.showerror("Error", "No customer loaded.")
            return

        info = (
            f"Name: {self.app.current_customer['full_name']}\n"
            f"Email: {self.app.current_customer['email']}\n"
            f"Contact: {self.app.current_customer['contact_number']}"
        )
        self.app.window.open_text_window("Customer Info", info)

    # ------------------------------------------------------------
    # CUSTOMER LOOKUP FOR ADMIN
    # ------------------------------------------------------------
    def customer_lookup_admin(self):
        name = simpledialog.askstring("Customer Lookup", "Enter customer name:", parent=self.app)
        if not name:
            return

        row = query("SELECT * FROM customer WHERE full_name LIKE ? LIMIT 1", ('%' + name + '%',), fetchone=True)
        if not row:
            messagebox.showerror("Not Found", "No customer found with that name.")
            return

        self.app.current_customer = row
        self.app.cart = []
        self.show_admin_customer_dashboard()
    
        self.app.current_customer = row
        self.app.cart = []
        self.show_admin_customer_dashboard()
