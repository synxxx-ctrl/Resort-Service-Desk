import customtkinter as ctk
from tkinter import messagebox
# Added 'execute' to imports for the delete function
from db import get_conn, query, execute
from models import CustomerModel
from utils import is_valid_email, is_valid_phone, generate_unique_customer_code

class CustomerController:
    def __init__(self, app):
        self.app = app

    # --- REGISTER ---
    def customer_register(self):
        self.app.window_manager.clear_container()
        
        frame = ctk.CTkFrame(self.app.container, fg_color="transparent")
        frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="Register New Customer", font=("Arial", 26, "bold")).pack(pady=(20, 30))
        
        form = ctk.CTkFrame(frame, corner_radius=10)
        form.pack(pady=10, padx=20)
        
        ctk.CTkLabel(form, text="Full Name:").grid(row=0, column=0, padx=20, pady=15, sticky="e")
        entry_name = ctk.CTkEntry(form, width=300); entry_name.grid(row=0, column=1, padx=20, pady=15)
        
        ctk.CTkLabel(form, text="Email Address:").grid(row=1, column=0, padx=20, pady=15, sticky="e")
        entry_email = ctk.CTkEntry(form, width=300); entry_email.grid(row=1, column=1, padx=20, pady=15)
        
        ctk.CTkLabel(form, text="Contact Number:").grid(row=2, column=0, padx=20, pady=15, sticky="e")
        entry_contact = ctk.CTkEntry(form, width=300); entry_contact.grid(row=2, column=1, padx=20, pady=15)

        def submit():
            name, email, contact = entry_name.get().strip(), entry_email.get().strip(), entry_contact.get().strip()
            if not name or not email or not contact:
                messagebox.showerror("Error", "All fields required.")
                return
            if not is_valid_email(email):
                messagebox.showerror("Error", "Invalid email.")
                return
            if not is_valid_phone(contact):
                messagebox.showerror("Error", "Invalid phone.")
                return
            try:
                code = generate_unique_customer_code()
                conn = get_conn(); cur = conn.cursor()
                cur.execute("INSERT INTO customer (username, full_name, email, contact_number) VALUES (?, ?, ?, ?)", (code, name, email, contact))
                cid = cur.lastrowid; conn.commit(); conn.close()
                self.app.current_customer = CustomerModel.get_customer_by_id(cid)
                self.app.cart = []
                # Jump to customer specific dashboard
                self.app.admin_dashboard.show_admin_customer_dashboard() 
            except Exception as e: messagebox.showerror("Error", f"DB Error: {e}")

        ctk.CTkButton(frame, text="Register & Continue", command=submit, width=200, height=45, fg_color="green").pack(pady=30)

    # --- LOOKUP ---
    def customer_lookup_admin(self):
        self.app.window_manager.clear_container()

        frame = ctk.CTkFrame(self.app.container, fg_color="transparent")
        frame.pack(expand=True, fill="both", padx=20, pady=20)

        ctk.CTkLabel(frame, text="Customer Lookup", font=("Arial", 26, "bold")).pack(pady=(10, 20))

        # Search Bar
        search_bar = ctk.CTkFrame(frame, fg_color="transparent")
        search_bar.pack(fill='x', padx=40)
        
        entry = ctk.CTkEntry(search_bar, placeholder_text="Search Name or Code...", height=40, font=("Arial", 14))
        entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        # Results Area
        results_area = ctk.CTkScrollableFrame(frame)
        results_area.pack(fill='both', expand=True, padx=40, pady=20)

        def perform_search(event=None):
            for w in results_area.winfo_children(): w.destroy()
            term = entry.get().strip()
            
            sql = "SELECT * FROM customer WHERE full_name LIKE ? OR username LIKE ?" if term else "SELECT * FROM customer ORDER BY customer_id DESC LIMIT 50"
            params = (f'%{term}%', f'%{term}%') if term else ()
            rows = query(sql, params, fetchall=True)

            if not rows:
                ctk.CTkLabel(results_area, text="No customers found.", text_color="gray").pack(pady=20)
                return

            for r in rows:
                btn_txt = f"{r['full_name']}  (ID: {r['username']})  |  📞 {r['contact_number']}"
                btn = ctk.CTkButton(
                    results_area, 
                    text=btn_txt, 
                    font=("Arial", 14), 
                    height=55,
                    fg_color=("gray85", "gray25"), 
                    text_color=("black", "white"),
                    anchor="w",
                    hover_color=("gray75", "gray35"),
                    command=lambda c=r: self.select_customer(c)
                )
                btn.pack(fill='x', pady=4)

        ctk.CTkButton(search_bar, text="Search", width=100, height=40, command=perform_search).pack(side='right')
        entry.bind("<Return>", perform_search)
        perform_search() # Load initial list

    def select_customer(self, row):
        self.app.current_customer = row
        self.app.cart = []
        # Swap view to Customer Dashboard
        self.app.admin_dashboard.show_admin_customer_dashboard()

    # --- NEW: DELETE FUNCTION ---
    def delete_current_customer(self):
        if not hasattr(self.app, 'current_customer') or not self.app.current_customer:
            return

        cust = self.app.current_customer
        name = cust['full_name']
        cid = cust['customer_id']

        # 1. Warning
        if not messagebox.askyesno("Delete Customer", f"Are you sure you want to delete {name}?\n\nThis cannot be undone."):
            return

        # 2. Check for active reservations/history to prevent breaking DB integrity
        # (Assuming we don't want to delete customers who have financial records)
        try:
            active_res = query("SELECT COUNT(*) as cnt FROM reservation WHERE customer_id=?", (cid,), fetchone=True)
            count = active_res['cnt'] if active_res else 0
            
            if count > 0:
                if not messagebox.askyesno("History Found", f"This customer has {count} reservation records.\nDeleting them might cause data issues or hide transaction history.\n\nForce Delete anyway?"):
                    return
            
            # 3. Execute Delete
            execute("DELETE FROM customer WHERE customer_id=?", (cid,))
            
            # 4. Success & Reset
            messagebox.showinfo("Success", "Customer deleted.")
            self.app.current_customer = None
            self.app.admin_dashboard.show_default_view()
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not delete customer.\nReason: {e}")

    def show_current_customer_info(self):
        if not self.app.current_customer: return
        cust = self.app.current_customer
        
        win = ctk.CTkToplevel(self.app)
        win.title("Profile")
        win.geometry("400x400")
        
        ctk.CTkLabel(win, text="👤", font=("Arial", 60)).pack(pady=20)
        ctk.CTkLabel(win, text=cust['full_name'], font=("Arial", 22, "bold")).pack()
        ctk.CTkLabel(win, text=cust['username'], text_color="gray").pack()
        
        info = ctk.CTkFrame(win)
        info.pack(fill="x", padx=20, pady=20)
        ctk.CTkLabel(info, text=f"Email: {cust['email']}").pack(pady=5)
        ctk.CTkLabel(info, text=f"Phone: {cust['contact_number']}").pack(pady=5)