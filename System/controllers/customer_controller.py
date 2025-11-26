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
        search_win = ctk.CTkToplevel(self.app)
        search_win.title("Customer Lookup")
        search_win.geometry("450x550")
        search_win.transient(self.app) 
        search_win.grab_set() 

        ctk.CTkLabel(search_win, text="Select Customer", font=("Arial", 20, "bold")).pack(pady=15)
        
        # Search Bar Area
        search_frame = ctk.CTkFrame(search_win, fg_color="transparent")
        search_frame.pack(fill='x', padx=20, pady=5)
        
        entry_search = ctk.CTkEntry(search_frame, placeholder_text="Search Name or Code...", height=35)
        entry_search.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        # Results Area
        results_frame = ctk.CTkScrollableFrame(search_win)
        results_frame.pack(fill='both', expand=True, padx=20, pady=10)

        def perform_search(event=None):
            for widget in results_frame.winfo_children(): widget.destroy()
            
            term = entry_search.get().strip()
            
            if term:
                rows = query("SELECT * FROM customer WHERE full_name LIKE ? OR username LIKE ?", 
                             (f'%{term}%', f'%{term}%'), fetchall=True)
            else:
                rows = query("SELECT * FROM customer ORDER BY customer_id DESC", fetchall=True)
            
            if not rows:
                ctk.CTkLabel(results_frame, text="No customers found.", text_color="gray").pack(pady=20)
                return
                
            for r in rows:
                btn_text = f"{r['full_name']}\nID: {r['username']} | 📞 {r['contact_number']}"
                
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

        ctk.CTkButton(search_frame, text="Search", width=80, height=35, command=perform_search).pack(side='right')
        
        entry_search.bind("<Return>", perform_search)
        
        # Initial Load
        perform_search()
        entry_search.focus()

    def show_current_customer_info(self):
        if not hasattr(self.app, 'current_customer') or not self.app.current_customer:
            messagebox.showerror("Error", "No customer loaded.", parent=self.app)
            return
        
        cust = self.app.current_customer

        # --- Modern Profile Window ---
        info_win = ctk.CTkToplevel(self.app)
        info_win.title("Customer Profile")
        # --- FIX: Increased Height to 500 to fit the Close button ---
        info_win.geometry("400x500")
        info_win.transient(self.app)
        info_win.grab_set()

        # Main Container
        main = ctk.CTkFrame(info_win, fg_color="transparent")
        main.pack(expand=True, fill="both", padx=20, pady=20)

        # 1. Avatar / Header
        ctk.CTkLabel(main, text="👤", font=("Arial", 60)).pack(pady=(10, 5))
        
        ctk.CTkLabel(main, text=cust['full_name'], font=("Arial", 22, "bold")).pack()
        ctk.CTkLabel(main, text=f"Customer ID: {cust['username']}", font=("Arial", 14), text_color="gray").pack(pady=(0, 15))

        # Divider
        ctk.CTkFrame(main, height=2, fg_color="gray60").pack(fill="x", padx=40, pady=10)

        # 2. Details Card
        details_card = ctk.CTkFrame(main, corner_radius=10, fg_color=("gray90", "gray20"))
        details_card.pack(fill="x", padx=10, pady=10)

        details_card.columnconfigure(0, weight=1)
        details_card.columnconfigure(1, weight=2)

        # Email
        ctk.CTkLabel(details_card, text="Email:", font=("Arial", 14, "bold"), anchor="e").grid(row=0, column=0, padx=10, pady=15, sticky="e")
        ctk.CTkLabel(details_card, text=cust['email'], font=("Arial", 14), anchor="w").grid(row=0, column=1, padx=10, pady=15, sticky="w")

        # Separator line inside card
        ctk.CTkFrame(details_card, height=1, fg_color="gray70").grid(row=1, column=0, columnspan=2, sticky="ew", padx=10)

        # Phone
        ctk.CTkLabel(details_card, text="Phone:", font=("Arial", 14, "bold"), anchor="e").grid(row=2, column=0, padx=10, pady=15, sticky="e")
        ctk.CTkLabel(details_card, text=cust['contact_number'], font=("Arial", 14), anchor="w").grid(row=2, column=1, padx=10, pady=15, sticky="w")

        # 3. Actions (Just Close)
        ctk.CTkButton(main, text="Close", command=info_win.destroy, fg_color="#c0392b", hover_color="#e74c3c", width=140).pack(pady=30)