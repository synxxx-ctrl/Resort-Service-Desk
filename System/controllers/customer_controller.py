import customtkinter as ctk
from tkinter import messagebox
import re
from db import get_conn, query
from models import CustomerModel
from utils import is_valid_email, is_valid_phone, generate_unique_customer_code

class CustomerController:
    def __init__(self, app):
        """
        Initialize the CustomerController.
        :param app: Reference to the main application class.
        """
        self.app = app

    def customer_register(self):
        self.app.window_manager.clear_container()
        
        # 1. UI Setup
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

            if not name or not email or not contact:
                messagebox.showerror("Error", "All fields are required.")
                return

            if not is_valid_email(email):
                messagebox.showerror("Invalid Email", "Please enter a valid email address.")
                return
            
            if not is_valid_phone(contact):
                messagebox.showerror("Invalid Number", "Please enter a valid phone number.")
                return

            try:
                customer_code = generate_unique_customer_code()
                
                conn = get_conn()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO customer (username, full_name, email, contact_number) VALUES (?, ?, ?, ?)",
                    (customer_code, name, email, contact)
                )
                customer_id = cur.lastrowid
                conn.commit()
                conn.close()

                self.app.current_customer = CustomerModel.get_customer_by_id(customer_id)
                self.app.cart = []

                self.app.admin_dashboard.show_admin_customer_dashboard()

            except Exception as e:
                messagebox.showerror("Database Error", f"An error occurred: {e}")

        # 3. Buttons
        btn_submit = ctk.CTkButton(self.app.container, text="Register & Continue", command=submit_form, fg_color="green")
        btn_submit.pack(pady=20)

        btn_back = ctk.CTkButton(
            self.app.container, 
            text="Cancel", 
            command=self.app.admin_dashboard.show_admin_interface, 
            fg_color="transparent", 
            border_width=1
        )
        btn_back.pack(pady=5)

    def customer_lookup_admin(self):
        # --- NEW: Small Window for Lookup ---
        search_win = ctk.CTkToplevel(self.app)
        search_win.title("Customer Lookup")
        search_win.geometry("400x500")
        search_win.transient(self.app) # Keep on top of main app
        search_win.grab_set() # Modal behavior

        ctk.CTkLabel(search_win, text="Find Customer", font=("Arial", 20, "bold")).pack(pady=15)
        
        # Search Bar Area
        search_frame = ctk.CTkFrame(search_win, fg_color="transparent")
        search_frame.pack(fill='x', padx=20, pady=5)
        
        entry_search = ctk.CTkEntry(search_frame, placeholder_text="Name or Customer Code", height=35)
        entry_search.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        # Results Area
        results_frame = ctk.CTkScrollableFrame(search_win)
        results_frame.pack(fill='both', expand=True, padx=20, pady=10)

        def perform_search(event=None):
            # Clear previous
            for widget in results_frame.winfo_children(): widget.destroy()
            
            term = entry_search.get().strip()
            if not term: return

            # Find matching customers
            rows = query("SELECT * FROM customer WHERE full_name LIKE ? OR username LIKE ?", 
                         (f'%{term}%', f'%{term}%'), fetchall=True)
            
            if not rows:
                ctk.CTkLabel(results_frame, text="No matches found.", text_color="gray").pack(pady=20)
                return
                
            for r in rows:
                # Create a card/button for each match
                btn_text = f"{r['full_name']}\nID: {r['username']} | 📞 {r['contact_number']}"
                
                # Using a Button that looks like a card
                btn = ctk.CTkButton(
                    results_frame, 
                    text=btn_text, 
                    font=("Arial", 14), 
                    height=60,
                    fg_color="transparent", 
                    border_width=1, 
                    border_color="gray",
                    text_color=("black", "white"),
                    anchor="w",
                    command=lambda cust=r: select_customer(cust)
                )
                btn.pack(fill='x', pady=5)

        def select_customer(row):
            self.app.current_customer = row
            self.app.cart = [] # Reset cart
            search_win.destroy() # Close lookup window
            self.app.admin_dashboard.show_admin_customer_dashboard()

        # Search Button
        ctk.CTkButton(search_frame, text="Search", width=80, height=35, command=perform_search).pack(side='right')
        
        # Allow pressing 'Enter' to search
        entry_search.bind("<Return>", perform_search)
        entry_search.focus()

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
        
        self.app.window_manager.open_text_window("Customer Info", info)