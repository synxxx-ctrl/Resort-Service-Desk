import customtkinter as ctk
from tkinter import messagebox, simpledialog
from models import AdminModel, CustomerModel, RoomModel
from utils import is_valid_email, is_valid_phone
import tkinter as tk
from db import query
from datetime import datetime, date, timedelta

try:
    from tkcalendar import DateEntry
    TKCALENDAR_AVAILABLE = True
except Exception:
    TKCALENDAR_AVAILABLE = False

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Resort Service Desk")
        self.geometry("1100x700")  # Big main window
        self.open_windows = {}
        self.current_customer = None
        self.cart = []
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(expand=True, fill="both")
        
        # Directly show admin login as a small centered frame
        self.open_admin_login()


    def open_admin_login(self):
        # Hide the main window
        self.withdraw()

        # --- CREATE SMALL LOGIN WINDOW ---
        login_win = ctk.CTkToplevel(self)
        login_win.title("Admin Login")
        login_win.geometry("320x260")
        login_win.resizable(False, False)
        login_win.grab_set()   # Prevent clicking anywhere else

        # Center the window
        login_win.update_idletasks()
        x = (login_win.winfo_screenwidth() // 2) - (320 // 2)
        y = (login_win.winfo_screenheight() // 2) - (260 // 2)
        login_win.geometry(f"320x260+{x}+{y}")

        # Title
        ctk.CTkLabel(login_win, text="Admin Login", font=("Helvetica", 20)).pack(pady=10)

        # Username
        ctk.CTkLabel(login_win, text="Username:").pack()
        username_var = tk.StringVar()
        username_entry = ctk.CTkEntry(login_win, width=200, textvariable=username_var)
        username_entry.pack(pady=5)

        # Password
        ctk.CTkLabel(login_win, text="Password:").pack()
        password_var = tk.StringVar()
        password_entry = ctk.CTkEntry(login_win, width=200, show="*", textvariable=password_var)
        password_entry.pack(pady=5)

        # Login Logic
        def attempt_login():
            username = username_var.get().strip()
            password = password_var.get().strip()

            if not username or not password:
                messagebox.showerror("Error", "Both fields are required.")
                return

            if AdminModel.check_login(username, password):
                login_win.destroy()   # close login window
                self.deiconify()      # show main window
                self.show_admin_interface()
            else:
                messagebox.showerror("Login Failed", "Incorrect username or password.")

        # ENTER KEY SUPPORT
        login_win.bind("<Return>", lambda event: attempt_login())

        # Proceed button
        ctk.CTkButton(login_win, text="Proceed", command=attempt_login).pack(pady=15)

        # Focus cursor on username
        username_entry.focus()
    
    # ------------------------- Main Menu -------------------------
    def show_main_menu(self):
        """Displays the main user-facing menu or initial screen."""
        self.geometry("1100x700")  # Set back to large size
        
        # --- SAFE SCREEN CLEARING ---
        # 1. Destroy all current widgets (including old containers)
        for widget in self.winfo_children():
            widget.destroy()
        # 2. Re-create the container so we have a place to put the new buttons
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)
        # ----------------------------
        # Main Menu Content
        ctk.CTkLabel(self.container, text="Welcome to the Main Menu", font=("Helvetica", 30)).pack(pady=50)
        
        # Updated Button: "Admin Login" (Removed "for testing")
        ctk.CTkButton(self.container, text="Admin Login", command=self.open_admin_login).pack(pady=10)
        
        # Reset admin mode flag
        self.is_admin_mode = False

    def show_customer_dashboard(self):
        self.clear_container()
        
        if not self.current_customer:
            ctk.CTkLabel(self.container, text="Error: No customer selected.", font=("Helvetica", 18)).pack(pady=50)
            ctk.CTkButton(self.container, text="Back to Main Menu", command=self.show_main_menu).pack(pady=10)
            return

        frame = ctk.CTkFrame(self.container, corner_radius=8)
        frame.pack(pady=20, padx=20, expand=True, fill="both")

        # Welcome and Info
        ctk.CTkLabel(frame, text=f"Welcome, {self.current_customer['full_name']}!", font=("Helvetica", 24)).pack(pady=10)
        
        info_frame = ctk.CTkFrame(frame, fg_color='transparent')
        info_frame.pack(pady=10, padx=20, fill='x')

        info_text = (
            f"Customer Code: **{self.current_customer['username']}**\n"
            f"Email: {self.current_customer['email']}\n"
            f"Contact: {self.current_customer['contact_number']}"
        )
        ctk.CTkLabel(info_frame, text=info_text, justify='left', font=("Helvetica", 14)).pack(anchor='w', padx=10)

        # Separator
        ctk.CTkFrame(frame, height=2, corner_radius=0, fg_color='gray').pack(fill='x', padx=5, pady=20)

        # Action Buttons
        ctk.CTkLabel(frame, text="Actions", font=("Helvetica", 18)).pack(pady=10)
        
        # Check if they have an active reservation (optional logic, but good practice)
        # active_res = CustomerModel.get_active_reservations(self.current_customer['customer_id'])
        
        ctk.CTkButton(frame, text="View Reservations", command=self.show_customer_reservations).pack(pady=10)
        ctk.CTkButton(frame, text="View Services and Billing", command=self.show_customer_services).pack(pady=10)
        ctk.CTkButton(frame, text="View Payments / Receipts", command=self.show_customer_transactions).pack(pady=10)
        
        # Back button to Admin/Main Menu (depending on how they logged in)
        if self.is_admin_mode:
            # Assuming you set self.is_admin_mode = True in open_admin_login
            ctk.CTkButton(frame, text="Back to Admin Customer Lookup", command=self.customer_lookup_admin).pack(pady=30)
        else:
            ctk.CTkButton(frame, text="Logout", command=self.show_main_menu).pack(pady=30)

    # ------------------------- Utilities -------------------------
    def clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def focus_or_create_window(self, key, create_fn):
        if key in self.open_windows and self.open_windows[key].winfo_exists():
            self.open_windows[key].focus()
            return
        w = create_fn()
        self.open_windows[key] = w
        def on_close():
            if key in self.open_windows:
                del self.open_windows[key]
            w.destroy()
        w.protocol("WM_DELETE_WINDOW", on_close)
        return w

    # ------------------------- Admin Login -------------------------
    def open_admin_login(self):
        # Hide main window immediately
        self.withdraw()

        # --- CREATE SMALL LOGIN WINDOW ---
        login_win = ctk.CTkToplevel(self)
        login_win.title("Resort Service Desk")
        login_win.geometry("320x260")
        login_win.resizable(False, False)
        login_win.grab_set()   # Make it modal (forces interaction here)

        # --- CENTER WINDOW ---
        login_win.update_idletasks()
        x = (login_win.winfo_screenwidth() // 2) - (320 // 2)
        y = (login_win.winfo_screenheight() // 2) - (260 // 2)
        login_win.geometry(f"320x260+{x}+{y}")

        # Title
        ctk.CTkLabel(login_win, text="Admin Login", font=("Helvetica", 20)).pack(pady=10)

        # Username
        ctk.CTkLabel(login_win, text="Username:").pack()
        username_var = tk.StringVar()
        ctk.CTkEntry(login_win, width=200, textvariable=username_var).pack(pady=5)

        # Password
        ctk.CTkLabel(login_win, text="Password:").pack()
        password_var = tk.StringVar()
        ctk.CTkEntry(login_win, width=200, show="*", textvariable=password_var).pack(pady=5)

        # Login Logic
        def attempt_login():
            username = username_var.get().strip()
            password = password_var.get().strip()

            if username == "" or password == "":
                messagebox.showerror("Error", "Both fields are required.")
                return
            
            if AdminModel.check_login(username, password):
                self.is_admin_mode = True
                login_win.destroy()    # Close login window
                self.deiconify()       # Show main window
                self.show_admin_interface()
            else:
                messagebox.showerror("Login Failed", "Incorrect username or password.")

        ctk.CTkButton(login_win, text="Proceed", command=attempt_login).pack(pady=15)


    # ------------------------- Admin Interface Placeholder -------------------------

    def show_admin_interface(self):
        # --- FIX: START ---
        # 1. Clear the WHOLE window (removes Registration form or old menus)
        for widget in self.winfo_children():
            widget.destroy()

        # 2. Re-create the main container
        # We must do this because customer_register destroyed the previous one
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)
        # --- FIX: END ---

        # 3. Create the inner frame for the menu
        frame = ctk.CTkFrame(self.container)
        frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="Admin Dashboard", font=("Helvetica", 30)).pack(pady=20)

        # ------------------- Reporting & Management -------------------
        ctk.CTkLabel(frame, text="Reporting & System Management", font=("Helvetica", 16)).pack(pady=10)
        ctk.CTkButton(frame, text="View Reservations", command=self.show_reservations).pack(pady=6)
        ctk.CTkButton(frame, text="View Transactions", command=self.show_transactions).pack(pady=6)
        ctk.CTkButton(frame, text="View Checked-in Guests", command=self.show_check_in_list).pack(pady=6)
        # Note: You had "View Checked-in Guests" listed twice in your code, I removed the duplicate.
        ctk.CTkButton(frame, text="Generate Report", command=self.generate_report).pack(pady=6)
        ctk.CTkButton(frame, text="Change Admin Credentials", command=self.change_admin_credentials).pack(pady=6)
        
        ctk.CTkFrame(frame, height=2, fg_color="gray35").pack(fill="x", pady=15)

        # ------------------- Customer Management (NEW) -------------------
        ctk.CTkLabel(frame, text="Customer Management", font=("Helvetica", 16)).pack(pady=10)
        ctk.CTkButton(frame, text="Customer Lookup (Name Search)", command=self.customer_lookup_admin).pack(pady=8)
        ctk.CTkButton(frame, text="New Customer / Register", command=self.customer_register).pack(pady=8)

        # ------------------- Back Button -------------------
        ctk.CTkButton(frame, text="Back", command=self.logout_admin).pack()

    def logout_admin(self):
        # Hide main window
        self.withdraw()

        # Destroy admin UI frame if it exists
        if hasattr(self, "admin_frame") and self.admin_frame.winfo_exists():
            self.admin_frame.destroy()

        # Return to login window
        self.open_admin_login()

    def show_reservations(self):
        rows = AdminModel.get_reservations()
        rows_dicts = [dict(r) for r in rows]  
        
        txt = "\n".join([
            f"{r['reservation_id']}: {r['full_name']} (code {r.get('customer_code','')}) — {r['check_in_date']} to {r['check_out_date']} — {r['status']}"
            for r in rows_dicts
        ])
        self.open_text_window("Reservations", txt or "No reservations available.")

    def show_transactions(self):
        from db import query
        rows = query("""
            SELECT p.payment_id, p.payment_method, p.amount, p.payment_date, c.full_name
            FROM payment p
            JOIN customer c ON c.customer_id = p.customer_id
            ORDER BY p.payment_date DESC
        """, fetchall=True)
        
        if not rows:
            self.open_text_window("Transactions", "No transactions available.")
            return

        txt = "\n".join([
            f"{r['payment_id']}: {r['full_name']} — {r['payment_method']} — ₱{r['amount']:.2f} — {r['payment_date']}"
            for r in rows
        ])
        self.open_text_window("Transactions", txt)

    def show_check_in_list(self):
        self.clear_container()
        frame = ctk.CTkScrollableFrame(self.container, corner_radius=8)
        frame.pack(pady=20, padx=20, expand=True, fill="both")

        ctk.CTkLabel(frame, text="Currently Checked-in Guests", font=("Helvetica", 22)).pack(pady=10)
        
        # Correct query using SUM(payment.amount)
        rows = query("""
            SELECT 
                r.*,
                c.full_name, 
                c.username AS customer_code, 
                rm.room_number,
                b.final_amount,
                IFNULL(SUM(p.amount), 0) AS amount_paid
            FROM reservation r
            JOIN customer c ON r.customer_id = c.customer_id
            LEFT JOIN room rm ON r.room_id = rm.room_id
            LEFT JOIN billing b ON r.reservation_id = b.reservation_id
            LEFT JOIN payment p ON p.billing_id = b.billing_id
            WHERE r.status = 'Checked-in'
            GROUP BY r.reservation_id
            ORDER BY r.check_in_date DESC
        """, fetchall=True)

        if not rows:
            ctk.CTkLabel(frame, text="No guests are currently checked-in.", font=("Helvetica", 16)).pack(pady=20)
        else:
            for row in rows:
                res_frame = ctk.CTkFrame(frame, corner_radius=6)
                res_frame.pack(fill='x', padx=10, pady=5)
                
                # Calculate balance
                final_amount = row['final_amount'] if row['final_amount'] is not None else 0
                amount_paid = row['amount_paid'] if row['amount_paid'] is not None else 0
                balance_due = final_amount - amount_paid

                info = (
                    f"ID: {row['reservation_id']} | Room: {row['room_number']} | Guests: {row['num_guests']}\n"
                    f"Customer: {row['full_name']} (Code: {row['customer_code']})\n"
                    f"Dates: {row['check_in_date']} to {row['check_out_date']} (Expected)\n"
                    f"Status: {row['status']} | Final Amount: ₱{final_amount:.2f}\n"
                    f"Paid: ₱{amount_paid:.2f} | Balance Due: ₱{balance_due:.2f}"
                )
                
                ctk.CTkLabel(res_frame, text=info, justify='left').pack(side='left', padx=10, pady=10, anchor='w')
                
                # Check-out button
                ctk.CTkButton(
                    res_frame, 
                    text="Check-out & Bill",
                    command=lambda res_id=row['reservation_id'], room_num=row['room_number']: 
                        self.show_check_out_process(res_id, room_num, row['room_id'])
                ).pack(side='right', padx=10, pady=10)

        ctk.CTkButton(frame, text="Back to Admin Menu", command=self.show_admin_interface).pack(pady=20)


    def show_check_out_process(self, reservation_id, room_number, room_id):
        self.clear_container()
        frame = ctk.CTkScrollableFrame(self.container, corner_radius=8)
        frame.pack(pady=20, padx=20, expand=True, fill="both")

        ctk.CTkLabel(frame, text=f"Check-out: Reservation #{reservation_id} (Room {room_number})", font=("Helvetica", 22)).pack(pady=10)
        
        reservation = query("SELECT r.*, c.full_name FROM reservation r JOIN customer c ON r.customer_id = c.customer_id WHERE r.reservation_id = ?", (reservation_id,), fetchone=True)
        if not reservation:
            messagebox.showerror("Error", "Reservation not found.")
            self.show_check_in_list()
            return
        
        # 1. Billing Summary
        # Ensure a billing record exists and is up-to-date
        CustomerModel.calculate_and_create_bill(reservation_id)
        billing = query("SELECT * FROM billing WHERE reservation_id = ?", (reservation_id,), fetchone=True)
        
        # Calculate Final Amount Due
        final_amount = billing['final_amount']
        amount_paid = billing['amount_paid']
        balance_due = final_amount - amount_paid

        # Display Billing Info
        bill_frame = ctk.CTkFrame(frame, fg_color='transparent')
        bill_frame.pack(fill='x', pady=10)
        ctk.CTkLabel(bill_frame, text="Billing Summary", font=("Helvetica", 18)).pack(pady=5)
        ctk.CTkLabel(bill_frame, text=f"Total Charges: ₱{final_amount:.2f}").pack(pady=2)
        ctk.CTkLabel(bill_frame, text=f"Amount Paid (Deposits/Initial): ₱{amount_paid:.2f}").pack(pady=2)
        
        balance_label = ctk.CTkLabel(bill_frame, text=f"BALANCE DUE: ₱{balance_due:.2f}", font=("Helvetica", 18), text_color='red' if balance_due > 0 else 'green')
        balance_label.pack(pady=5)

        # 2. Payment Section
        ctk.CTkFrame(frame, height=2, corner_radius=0, fg_color='gray').pack(fill='x', padx=5, pady=15)
        ctk.CTkLabel(frame, text="Process Final Payment", font=("Helvetica", 18)).pack(pady=5)

        amount_var = tk.StringVar(value=f"{balance_due:.2f}" if balance_due > 0 else "0.00")
        payment_methods = ['Cash', 'Credit Card', 'Bank Transfer', 'No Payment Due']
        method_var = tk.StringVar(value='No Payment Due' if balance_due <= 0 else payment_methods[0])
        
        ctk.CTkLabel(frame, text="Payment Amount:").pack(pady=2)
        amount_entry = ctk.CTkEntry(frame, textvariable=amount_var, state='normal' if balance_due > 0 else 'disabled')
        amount_entry.pack(pady=2)

        ctk.CTkLabel(frame, text="Payment Method:").pack(pady=2)
        method_menu = ctk.CTkOptionMenu(frame, variable=method_var, values=payment_methods)
        method_menu.pack(pady=2)

        def finalize_checkout():
            try:
                pay_amount = float(amount_var.get())
            except ValueError:
                messagebox.showerror("Error", "Invalid payment amount.")
                return
            
            method = method_var.get()
            
            # Balance validation
            if balance_due > 0 and pay_amount < balance_due and method != 'No Payment Due':
                messagebox.showerror("Error", f"Payment amount (₱{pay_amount:.2f}) is less than the balance due (₱{balance_due:.2f}).")
                return
            
            if pay_amount < 0:
                messagebox.showerror("Error", "Payment amount cannot be negative.")
                return

            try:
                # 1. Record the payment if amount > 0
                if pay_amount > 0:
                    CustomerModel.record_payment(reservation_id, reservation['customer_id'], pay_amount, method)
                
                # 2. Finalize Check-out in the database
                CustomerModel.checkout_reservation(reservation_id)
                
                # 3. Mark room as available
                query("UPDATE room SET status='available' WHERE room_id=?", (room_id,))
                
                messagebox.showinfo("Success", f"Reservation #{reservation_id} checked out successfully. Room {room_number} is now available.")
                self.show_check_in_list() # Return to the check-in list
                
            except Exception as e:
                messagebox.showerror("Database Error", f"Failed to finalize check-out: {e}")
                
        # Checkout button command
        checkout_btn = ctk.CTkButton(frame, text="FINALIZE CHECK-OUT", command=finalize_checkout)
        checkout_btn.pack(pady=20)
        
        ctk.CTkButton(frame, text="Back to Check-in List", command=self.show_check_in_list).pack(pady=10)

    def generate_report(self):
        win = ctk.CTkToplevel(self)
        win.title("Generate Report")
        win.geometry("360x320")

        ctk.CTkLabel(win, text="Choose Report Type", font=("Helvetica", 18)).pack(pady=12)

        ctk.CTkButton(
            win, text="Full Report (All-Time)",
            width=300, command=lambda: (win.destroy(), self.generate_full_report())
        ).pack(pady=6)

        ctk.CTkButton(
            win, text="Report For Specific Date",
            width=300, command=lambda: (win.destroy(), self.generate_daily_report_prompt())
        ).pack(pady=6)

        ctk.CTkButton(
            win, text="Weekly Report (Last 7 Days)",
            width=300, command=lambda: (win.destroy(), self.generate_weekly_report())
        ).pack(pady=6)

        ctk.CTkButton(
            win, text="Monthly Report (Last 30 Days)",
            width=300, command=lambda: (win.destroy(), self.generate_monthly_report())
        ).pack(pady=6)

        ctk.CTkButton(
            win, text="Custom Date Range",
            width=300, command=lambda: (win.destroy(), self.generate_range_prompt())
        ).pack(pady=6)

        ctk.CTkButton(
            win, text="Cancel", width=300,
            command=win.destroy
        ).pack(pady=8)

    # ------------------------- Reports -------------------------
    def generate_full_report(self):
        from db import query

        try:
            rows = query("""
                SELECT
                    r.reservation_id,
                    c.full_name,
                    r.check_in_date,
                    r.check_out_date,
                    r.status,
                    IFNULL(b.final_amount, 0) AS final_amount,
                    b.status AS billing_status
                FROM reservation r
                LEFT JOIN customer c ON r.customer_id = c.customer_id
                LEFT JOIN billing b ON b.reservation_id = r.reservation_id
                ORDER BY r.reservation_id DESC
            """, fetchall=True)

            if not rows:
                self.open_text_window("Full Report", "No reservation data found.")
                return

            txt = ""
            for r in rows:
                txt += (
                    f"Reservation ID: {r['reservation_id']}\n"
                    f"Customer: {r['full_name']}\n"
                    f"Check-in: {r['check_in_date']}\n"
                    f"Check-out: {r['check_out_date']}\n"
                    f"Reservation Status: {r['status']}\n"
                    f"Billing Amount: ₱{r['final_amount']}\n"
                    f"Billing Status: {r['billing_status']}\n"
                    f"{'-'*60}\n"
                )

            self.open_text_window("Full Report", txt)

        except Exception as e:
            messagebox.showerror("DB Error", f"Could not generate full report:\n{e}")

    def generate_daily_report_prompt(self):
        date_str = simpledialog.askstring(
            "Daily Report",
            "Enter date (YYYY-MM-DD):",
            parent=self
        )
        if not date_str:
            return
        
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except:
            messagebox.showerror("Invalid Date", "Please use YYYY-MM-DD format.")
            return
        
        self.generate_range_report(date_str, date_str, f"Daily Report - {date_str}")

    def generate_daily_report(self, date_str):
        # kept for backward compatibility (calls range reporter)
        self.generate_range_report(date_str, date_str, f"Daily Report - {date_str}")

    def generate_weekly_report(self):
        end = date.today()
        start = end - timedelta(days=6)  # last 7 days inclusive
        self.generate_range_report(start.isoformat(), end.isoformat(), "Weekly Report (Last 7 Days)")

    def generate_monthly_report(self):
        end = date.today()
        start = end - timedelta(days=29)  # last 30 days inclusive
        self.generate_range_report(start.isoformat(), end.isoformat(), "Monthly Report (Last 30 Days)")

    def generate_range_prompt(self):
        start_str = simpledialog.askstring("Report Start Date", "Enter start date (YYYY-MM-DD):", parent=self)
        if not start_str:
            return
        end_str = simpledialog.askstring("Report End Date", "Enter end date (YYYY-MM-DD):", parent=self)
        if not end_str:
            return
        # validate
        try:
            s = datetime.strptime(start_str, "%Y-%m-%d").date()
            e = datetime.strptime(end_str, "%Y-%m-%d").date()
            if e < s:
                messagebox.showerror("Invalid Range", "End date must be the same or after start date.")
                return
        except Exception:
            messagebox.showerror("Invalid Date", "Please use YYYY-MM-DD format.")
            return
        self.generate_range_report(start_str, end_str, f"Report: {start_str} to {end_str}")

    def generate_range_report(self, start_date_str, end_date_str, title):
        from db import query

        try:
            rows = query("""
                SELECT
                    r.reservation_id,
                    c.full_name,
                    r.check_in_date,
                    r.check_out_date,
                    r.num_guests,
                    r.status,
                    IFNULL(b.final_amount, 0) AS final_amount,
                    b.status AS billing_status
                FROM reservation r
                LEFT JOIN customer c ON r.customer_id = c.customer_id
                LEFT JOIN billing b ON b.reservation_id = r.reservation_id
                WHERE DATE(r.check_in_date) BETWEEN ? AND ?
                   OR DATE(r.check_out_date) BETWEEN ? AND ?
                ORDER BY r.reservation_id DESC
            """, (start_date_str, end_date_str, start_date_str, end_date_str), fetchall=True)

            if not rows:
                self.open_text_window(title, f"No reservations found between {start_date_str} and {end_date_str}.")
                return

            lines = []
            for r in rows:
                lines.append(
                    f"Reservation #{r['reservation_id']}\n"
                    f"  Name: {r['full_name']}\n"
                    f"  Check-in: {r['check_in_date']}\n"
                    f"  Check-out: {r['check_out_date']}\n"
                    f"  Guests: {r.get('num_guests', '')}\n"
                    f"  Status: {r['status']}\n"
                    f"  Billing: ₱{r['final_amount']} ({r['billing_status']})\n"
                    + ("-"*40)
                )

            report_text = "\n".join(lines)
            self.open_text_window(title, report_text)

        except Exception as e:
            messagebox.showerror("DB Error", f"Could not generate report:\n{e}")

    def customer_lookup_admin(self):
        name = simpledialog.askstring("Customer Lookup", "Enter customer name:", parent=self)
        if not name:
            return
        row = query("SELECT * FROM customer WHERE full_name LIKE ? LIMIT 1", ('%' + name + '%',), fetchone=True)
        if not row:
            messagebox.showerror("Not Found", "No customer found with that name.")
            return
        self.current_customer = row
        self.cart = []
        self.show_admin_customer_dashboard()

    # ------------------------- Admin helper bugfix (SQL) -------------------------
    def change_admin_credentials(self):
        new_user = simpledialog.askstring("Change Admin Username", "New username:", parent=self)
        new_pass = simpledialog.askstring("Change Admin Password", "New password:", parent=self, show='*')
        if not new_user or not new_pass:
            messagebox.showerror("Error", "Both fields are required.")
            return
        from db import execute, query
        row = query("SELECT admin_id FROM admin LIMIT 1", fetchone=True)
        if row:
            # fixed typos: single ? placeholders
            execute("UPDATE admin SET username=?, password=? WHERE admin_id=?", (new_user, new_pass, row['admin_id']))
            messagebox.showinfo("Success", "Admin credentials updated.")
        else:
            messagebox.showerror("Error", "Admin record not found.")

    # ------------------------- Customer entry -------------------------

    def customer_lookup(self):
        name = simpledialog.askstring("Customer Lookup", "Enter customer name:", parent=self)
        if not name:
            return
        row = query("SELECT * FROM customer WHERE full_name LIKE ? LIMIT 1", ('%' + name + '%',), fetchone=True)
        if not row:
            messagebox.showerror("Not Found", "No customer found with that name.")
            return
        self.current_customer = row
        self.cart = []
        self.show_admin_customer_dashboard()

    def customer_register(self):
        # 1. Clear the current frame/window
        # CHANGED: self.root -> self
        for widget in self.winfo_children():
            widget.destroy()

        # 2. UI Setup
        import customtkinter as ctk 

        # Title
        # CHANGED: self.root -> self
        ctk.CTkLabel(self, text="Customer Registration", font=("Arial", 24, "bold")).pack(pady=30)

        # Form Frame
        # CHANGED: self.root -> self
        form_frame = ctk.CTkFrame(self)
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

        # 3. Submit Logic
        def submit_form():
            name = entry_name.get().strip()
            email = entry_email.get().strip()
            contact = entry_contact.get().strip()

            # Basic Validation
            if not name or not email or not contact:
                from tkinter import messagebox
                messagebox.showerror("Error", "All fields are required.")
                return

            if not is_valid_email(email):
                from tkinter import messagebox
                messagebox.showerror("Invalid Email", "Please enter a valid email address.")
                return
            
            if not is_valid_phone(contact):
                from tkinter import messagebox
                messagebox.showerror("Invalid Number", "Please enter a valid phone number.")
                return

            # Database Insert
            from db import get_conn
            from models import CustomerModel

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
                self.current_customer = CustomerModel.get_customer_by_id(customer_id)
                self.cart = []

                # Go to Dashboard
                self.show_admin_customer_dashboard()

            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror("Database Error", f"An error occurred: {e}")

        # 4. Buttons
        # CHANGED: self.root -> self
        btn_submit = ctk.CTkButton(self, text="Register & Continue", command=submit_form, fg_color="green")
        btn_submit.pack(pady=20)

        # Back Button
        # CHANGED: self.root -> self
        btn_back = ctk.CTkButton(self, text="Cancel", command=self.show_admin_interface, fg_color="transparent", border_width=1)
        btn_back.pack(pady=5)


    # ------------------------- Customer dashboard -------------------------
    def show_admin_customer_dashboard(self):
        if not self.current_customer:
            messagebox.showerror("Error", "No customer loaded.")
            return
        self.clear_container()
        frame = ctk.CTkScrollableFrame(self.container)
        frame.pack(pady=12, padx=12, expand=True, fill="both")
        
        ctk.CTkLabel(frame, text=f"Servicing Customer: {self.current_customer['full_name']} (ID: {self.current_customer['username']})", font=("Helvetica", 22)).pack(pady=8)
        
        ctk.CTkButton(frame, text="Make a Reservation", width=240, command=self.show_make_reservation).pack(pady=8)
        ctk.CTkButton(frame, text="Check-in Right Now (No dates)", width=240, command=self.check_in_now).pack(pady=8)
        ctk.CTkButton(frame, text="View Customer Info", width=240, command=self.show_current_customer_info).pack(pady=8)
        ctk.CTkButton(frame, text="Process Payment", width=240, command=self.show_make_payment).pack(pady=8)
        ctk.CTkButton(frame, text="View Receipts", width=240, command=self.show_receipts).pack(pady=8)

        # The admin returns to the main admin interface
        ctk.CTkButton(frame, text="Back to Admin Menu", width=240, command=self.show_admin_interface).pack(pady=16)

    def show_current_customer_info(self):
        if not self.current_customer:
            messagebox.showerror("Error", "No customer loaded.")
            return
        info = (
            f"Name: {self.current_customer['full_name']}\n"
            f"Email: {self.current_customer['email']}\n"
            f"Contact: {self.current_customer['contact_number']}"
        )
        self.open_text_window("Customer Info", info)

    # ------------------------- Reservation flow -------------------------

    def open_room_selection(self, rooms, num_guests):
        def create_dialog():
            dialog = ctk.CTkToplevel(self)
            dialog.title("Select an Available Room")
            dialog.geometry("500x400")
            dialog.transient(self)
            dialog.grab_set()

            ctk.CTkLabel(dialog, text=f"Select Room for {num_guests} Guests", font=("Helvetica", 18)).pack(pady=10)
            
            scroll_frame = ctk.CTkScrollableFrame(dialog)
            scroll_frame.pack(padx=10, pady=5, fill="both", expand=True)

            self.room_selection_dialog_var = tk.StringVar(value=self.room_id_var.get())
            selected_room_id = self.room_id_var.get() if self.room_id_var.get() != "0" else None
            
            room_info_map = {}
            for room in rooms:
                room_info_map[str(room['room_id'])] = room
                
                # Determine if room capacity is sufficient
                is_capacity_ok = room['room_capacity'] >= num_guests
                capacity_text = f"Capacity: {room['room_capacity']}"
                if not is_capacity_ok:
                    capacity_text += " (TOO SMALL)"
                
                # Radio button text
                room_display = f"Room {room['room_number']} - {capacity_text}"
                
                radio_btn = ctk.CTkRadioButton(scroll_frame, 
                    text=room_display, 
                    variable=self.room_selection_dialog_var, 
                    value=str(room['room_id']), 
                    state='normal' if is_capacity_ok else 'disabled')
                radio_btn.pack(anchor='w', padx=10, pady=4)
                
                # Select the previously selected room if capacity is still okay
                if str(room['room_id']) == selected_room_id and is_capacity_ok:
                    radio_btn.select()
                
            def on_confirm():
                selected_id = self.room_selection_dialog_var.get()
                if selected_id == "":
                    messagebox.showerror("Error", "Please select a room.")
                    return
                
                room = room_info_map.get(selected_id)
                if not room:
                    messagebox.showerror("Error", "Invalid room selection.")
                    return
                    
                # Update main window variables
                self.room_id_var.set(selected_id)
                self.room_selection_display_var.set(f"Room {room['room_number']} Selected")
                self.room_capacity = room['room_capacity']
                self.room_capacity_label.configure(text=f"Capacity: {self.room_capacity}")
                dialog.destroy()
                
            ctk.CTkButton(dialog, text="Confirm Selection", command=on_confirm).pack(pady=10)
            ctk.CTkButton(dialog, text="Cancel", command=dialog.destroy).pack(pady=5)
            
            return dialog

        self.focus_or_create_window('room_selection', create_dialog)

    def show_make_reservation(self):
        self.cart = []
        self.clear_container()
        frame = ctk.CTkFrame(self.container)
        frame.pack(pady=12, padx=12, expand=True, fill="both")
        left = ctk.CTkFrame(frame)
        left.pack(side="left", expand=True, fill="both", padx=12, pady=12)
        right = ctk.CTkFrame(frame, width=320)
        right.pack(side="right", fill="y", padx=12, pady=12)

        ctk.CTkLabel(left, text="Create Reservation", font=("Helvetica", 18)).pack(pady=8)

        # Dates
        date_frame = ctk.CTkFrame(left)
        date_frame.pack(pady=6)
        if TKCALENDAR_AVAILABLE:
            ctk.CTkLabel(date_frame, text="Check-in:").grid(row=0, column=0, padx=6, pady=6, sticky="e")
            checkin_widget = DateEntry(date_frame, width=14)
            checkin_widget.grid(row=0, column=1, padx=6, pady=6)
            ctk.CTkLabel(date_frame, text="Check-out:").grid(row=0, column=2, padx=6, pady=6, sticky="e")
            checkout_widget = DateEntry(date_frame, width=14)
            checkout_widget.grid(row=0, column=3, padx=6, pady=6)
        else:
            ctk.CTkLabel(date_frame, text="Check-in (YYYY-MM-DD):").grid(row=0, column=0, padx=6, pady=6, sticky="e")
            checkin_widget = ctk.CTkEntry(date_frame, width=14)
            checkin_widget.grid(row=0, column=1, padx=6, pady=6)
            ctk.CTkLabel(date_frame, text="Check-out (YYYY-MM-DD):").grid(row=0, column=2, padx=6, pady=6, sticky="e")
            checkout_widget = ctk.CTkEntry(date_frame, width=14)
            checkout_widget.grid(row=0, column=3, padx=6, pady=6)

        # Guests
        guests_var = tk.StringVar(value="1")
        ctk.CTkLabel(left, text="Number of guests:").pack(pady=6)
        guests_entry = ctk.CTkEntry(left, width=120, textvariable=guests_var)
        guests_entry.pack(pady=4)
        

        # Room Selection (NEW SECTION)
        ctk.CTkFrame(left, height=2, corner_radius=0, fg_color='gray').pack(fill='x', padx=5, pady=15)
        ctk.CTkLabel(left, text="Room Selection:", font=("Helvetica", 14)).pack(pady=8)

        self.room_id_var = tk.StringVar(value="0") # Stores the selected room_id
        self.room_capacity = 0 # Stores the capacity for validation

        self.room_selection_display_var = tk.StringVar(value="Select a Room (Click Check Availability)")
        self.room_selection_label = ctk.CTkLabel(left, textvariable=self.room_selection_display_var)
        self.room_selection_label.pack(pady=2)

        self.room_capacity_label = ctk.CTkLabel(left, text="Capacity: N/A")
        self.room_capacity_label.pack(pady=2)

        def check_availability_and_select():
            # 1. Date and Guest validation
            try:
                if TKCALENDAR_AVAILABLE:
                    checkin = checkin_widget.get_date()
                    checkout = checkout_widget.get_date()
                else:
                    s_in = checkin_widget.get()
                    s_out = checkout_widget.get()
                    # You might need to import datetime if not already done: from datetime import datetime, date
                    checkin = datetime.strptime(s_in.strip(), '%Y-%m-%d').date()
                    checkout = datetime.strptime(s_out.strip(), '%Y-%m-%d').date()
                
                if checkout <= checkin:
                    messagebox.showerror('Date Error','Check-out must be after check-in')
                    return
                
                guests = int(str(guests_var.get()).strip())
                if guests <= 0:
                    messagebox.showerror('Guests','Enter a valid number of guests')
                    return

            except Exception:
                messagebox.showerror('Input Error','Please enter valid dates (YYYY-MM-DD) and a valid number of guests.')
                return

            # 2. Get Available Rooms & Open Selection Dialog
            # NOTE: RoomModel.get_available_rooms must be in models.py
            rooms = RoomModel.get_available_rooms(checkin.isoformat(), checkout.isoformat())
            if not rooms:
                messagebox.showerror("No Rooms", "No available rooms for the selected dates.")
                self.room_id_var.set("0")
                self.room_selection_display_var.set("NO AVAILABLE ROOMS")
                self.room_capacity = 0
                self.room_capacity_label.configure(text="Capacity: N/A")
                return
            
            # NOTE: This calls the open_room_selection method you need to insert (see next section)
            self.open_room_selection(rooms, guests)

        ctk.CTkButton(left, text="Check Availability & Select Room", command=check_availability_and_select).pack(pady=6)


        # Services list 
        from db import query
        services = query("SELECT service_id, service_name, base_price FROM service", fetchall=True) or []
        ctk.CTkLabel(left, text="Available services:", font=("Helvetica", 14)).pack(pady=8)

        svc_list_frame = ctk.CTkScrollableFrame(left, height=280)
        svc_list_frame.pack(fill="both", expand=True, padx=6)

        svc_controls = [] 

        def add_to_cart(service_id, name, price, qty_var, mode_var):
            try:
                qty = int(str(qty_var.get()).strip())
                if qty <= 0:
                    messagebox.showerror("Invalid qty", "Quantity must be at least 1")
                    return
            except Exception:
                messagebox.showerror("Invalid qty", "Quantity must be a positive integer")
                return
            for item in self.cart:
                if item['service_id'] == service_id and item['mode'] == mode_var.get():
                    item['qty'] += qty
                    self.update_cart_preview(right)
                    return
            self.cart.append({
                'service_id': service_id,
                'name': name,
                'unit_price': price,
                'qty': qty,
                'mode': mode_var.get()
            })
            self.update_cart_preview(right)

        for svc in services:
            sid = svc['service_id']
            name = svc['service_name']
            price = svc['base_price']
            rowf = ctk.CTkFrame(svc_list_frame)
            rowf.pack(fill='x', pady=4, padx=6)
            lbl = ctk.CTkLabel(rowf, text=f"{name} (₱{price})")
            lbl.pack(side='left')
            qty_var = tk.StringVar(value='1')
            qty_entry = ctk.CTkEntry(rowf, width=60, textvariable=qty_var)
            qty_entry.pack(side='right', padx=6)
            mode_var = tk.StringVar(value='public')
            rm = ctk.CTkOptionMenu(rowf, values=['public','private'], variable=mode_var, width=100)
            rm.pack(side='right', padx=6)
            add_btn = ctk.CTkButton(rowf, text='Add', width=60, command=lambda s=sid, n=name, p=price, q=qty_var, m=mode_var: add_to_cart(s,n,p,q,m))
            add_btn.pack(side='right', padx=6)
            svc_controls.append((sid, name, price, qty_var, mode_var, add_btn))

        ctk.CTkLabel(right, text="Cart Preview", font=("Helvetica", 16)).pack(pady=8)
        cart_frame = ctk.CTkFrame(right)
        cart_frame.pack(fill='both', expand=True, padx=6, pady=6)

        self.cart_items_container = ctk.CTkScrollableFrame(cart_frame, height=380)
        self.cart_items_container.pack(fill='both', expand=True, padx=4, pady=4)

        totals_frame = ctk.CTkFrame(right)
        totals_frame.pack(fill='x', pady=6)
        self.total_label = ctk.CTkLabel(totals_frame, text='Total: ₱0.00', font=(None, 14))
        self.total_label.pack(side='left', padx=8)

        def clear_cart_action():
            if messagebox.askyesno('Clear Cart','Remove all items from cart?'):
                self.cart = []
                self.update_cart_preview(right)

        btns = ctk.CTkFrame(right)
        btns.pack(pady=8)
        ctk.CTkButton(btns, text='Clear Cart', command=clear_cart_action).pack(side='left', padx=6)
        ctk.CTkButton(btns, text='Confirm Reservation', fg_color='#2aa198', command=lambda: self.confirm_reservation(checkin_widget, checkout_widget, guests_var)).pack(side='left', padx=6)
        ctk.CTkButton(btns, text='Cancel', command=self.show_customer_dashboard).pack(side='left', padx=6)

        self.update_cart_preview(right)

    def update_cart_preview(self, parent_frame=None):
        try:
            container = self.cart_items_container
        except AttributeError:
            return
        for w in container.winfo_children():
            w.destroy()
        total = 0.0
        for idx, item in enumerate(self.cart, start=1):
            row = ctk.CTkFrame(container)
            row.pack(fill='x', pady=4, padx=6)
            ctk.CTkLabel(row, text=f"{item['name']} ({item['mode']}) x{item['qty']}").pack(side='left')
            subtotal = item['unit_price'] * item['qty']
            total += subtotal
            ctk.CTkLabel(row, text=f"₱{subtotal:.2f}").pack(side='right')
            def make_rm(i):
                return lambda: (self.cart.pop(i), self.update_cart_preview(parent_frame))
            ctk.CTkButton(row, text='Remove', width=80, command=make_rm(idx-1)).pack(side='right', padx=6)
        self.total_label.configure(text=f"Total: ₱{total:.2f}")

    def confirm_reservation(self, checkin_widget, checkout_widget, guests_var):
        if TKCALENDAR_AVAILABLE:
            try:
                checkin = checkin_widget.get_date()
                checkout = checkout_widget.get_date()
            except Exception:
                messagebox.showerror('Date error','Please select valid dates')
                return
        else:
            s_in = checkin_widget.get()
            s_out = checkout_widget.get()
            try:
                checkin = datetime.strptime(s_in.strip(), '%Y-%m-%d').date()
                checkout = datetime.strptime(s_out.strip(), '%Y-%m-%d').date()
            except Exception:
                messagebox.showerror('Date error','Please enter dates in YYYY-MM-DD')
                return
        if checkout < checkin:
            messagebox.showerror('Date error','Check-out must be after check-in')
            return
        try:
            guests = int(str(guests_var.get()).strip())
            if guests <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror('Guests','Enter a valid number of guests')
            return
        total = sum(item['unit_price'] * item['qty'] for item in self.cart)
        items_summary = '\n'.join([f"{i['name']} ({i['mode']}) x{i['qty']} = ₱{i['unit_price']*i['qty']:.2f}" for i in self.cart])
        confirm = messagebox.askyesno('Confirm Reservation', f"Check-in: {checkin}\nCheck-out: {checkout}\nGuests: {guests}\n\nServices:\n{items_summary if items_summary else 'No services selected'}\n\nTotal: ₱{total:.2f}\n\nProceed to save reservation?")
        if not confirm:
            return
        # Save to DB
        from db import get_conn
        try:
            conn = get_conn()
            cur = conn.cursor()
            created_at = datetime.now().isoformat(sep=' ', timespec='seconds')
            cur.execute(
                "INSERT INTO reservation (customer_id, check_in_date, check_out_date, num_guests, status, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (self.current_customer['customer_id'], checkin.isoformat(), checkout.isoformat(), guests, 'Pending', '', created_at)
            )
            reservation_id = cur.lastrowid
            for item in self.cart:
                cur.execute(
                    "INSERT INTO reservation_services (reservation_id, service_id, quantity, service_price) VALUES (?, ?, ?, ?)",
                    (reservation_id, item['service_id'], item['qty'], item['unit_price'])
                )
            cur.execute(
                "INSERT INTO billing (reservation_id, final_amount, status, created_at) VALUES (?, ?, ?, ?)",
                (reservation_id, total, 'Unpaid', created_at)
            )
            billing_id = cur.lastrowid
            conn.commit()
            conn.close()
            messagebox.showinfo('Saved', f"Reservation saved. ID: {reservation_id}. Billing ID: {billing_id}")
            self.cart = []
            self.show_admin_customer_dashboard() # NEW
        except Exception as e:
            messagebox.showerror('DB Error', f"Failed to save reservation: {e}")

    # ------------------------- Check-in now -------------------------
    def check_in_now(self):
        if not self.current_customer:
            messagebox.showerror("Error", "No customer loaded.")
            return
        s_in = simpledialog.askstring("Check-in time", "Enter check-in time (HH:MM, 24h). Example: 14:30", parent=self)
        s_out = simpledialog.askstring("Check-out time", "Enter check-out time (HH:MM, 24h). Example: 18:00", parent=self)
        if not s_in or not s_out:
            return
        try:
            t_in = datetime.strptime(s_in.strip(), "%H:%M").time()
            t_out = datetime.strptime(s_out.strip(), "%H:%M").time()
        except Exception:
            messagebox.showerror("Invalid time", "Time must be in HH:MM 24-hour format.")
            return
        from db import query, get_conn
        services = query("SELECT service_id, service_name, base_price FROM service", fetchall=True) or []
        if not services:
            messagebox.showerror("No services", "No services found in DB.")
            return
        svc_names = [f"{s['service_id']} - {s['service_name']} (₱{s['base_price']})" for s in services]
        svc_choice = simpledialog.askstring("Service", f"Pick service by entering its ID. Options:\n" + "\n".join(svc_names), parent=self)
        if not svc_choice:
            return
        try:
            svc_id = int(svc_choice.split()[0])
        except Exception:
            messagebox.showerror("Invalid choice", "Provide a service id number from the list.")
            return
        mode_choice = simpledialog.askstring("Mode", "Enter 'public' or 'private'", parent=self)
        if not mode_choice or mode_choice.lower() not in ("public","private"):
            messagebox.showerror("Invalid", "Mode must be 'public' or 'private'.")
            return
        mode_choice = mode_choice.lower()
        g = simpledialog.askstring("Guests", "Number of guests (integer):", parent=self)
        try:
            num_guests = int(str(g).strip())
            if num_guests <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror("Invalid", "Enter a valid integer for guests.")
            return
        today = date.today()
        checkin_dt = datetime.combine(today, t_in)
        checkout_dt = datetime.combine(today, t_out)
        if checkout_dt <= checkin_dt:
            checkout_dt += timedelta(days=1)
        try:
            conn = get_conn()
            cur = conn.cursor()
            created_at = datetime.now().isoformat(sep=' ', timespec='seconds')
            cur.execute(
                "INSERT INTO reservation (customer_id, check_in_date, check_out_date, num_guests, status, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (self.current_customer['customer_id'], checkin_dt.isoformat(sep=' '), checkout_dt.isoformat(sep=' '), num_guests, 'Checked-in', f"Mode:{mode_choice}", created_at)
            )
            reservation_id = cur.lastrowid
            svc_row = None
            for s in services:
                if s['service_id'] == svc_id:
                    svc_row = s
                    break
            price = svc_row['base_price'] if svc_row else 0.0
            cur.execute(
                "INSERT INTO reservation_services (reservation_id, service_id, quantity, service_price) VALUES (?, ?, ?, ?)",
                (reservation_id, svc_id, 1, price)
            )
            cur.execute(
                "INSERT INTO billing (reservation_id, final_amount, status, created_at) VALUES (?, ?, ?, ?)",
                (reservation_id, price, 'Paid', created_at)
            )
            billing_id = cur.lastrowid
            conn.commit()
            conn.close()
            messagebox.showinfo("Checked-in", f"Checked in successfully. Reservation ID: {reservation_id}")
        # self.show_customer_dashboard() # REMOVE/CHANGE
            self.show_admin_customer_dashboard() # NEW
        except Exception as e:
            messagebox.showerror("DB Error", f"Failed to save check-in: {e}")

    def show_make_payment(self):
        if not self.current_customer:
            messagebox.showerror("Error", "No customer loaded.")
            return
        self.clear_container()
        frame = ctk.CTkScrollableFrame(self.container)
        frame.pack(pady=12, padx=12, expand=True, fill="both")
        
        ctk.CTkLabel(frame, text="Make a Payment", font=("Helvetica", 22)).pack(pady=8)
        
        from db import query, execute
        rows = query("""
            SELECT r.reservation_id, r.check_in_date, r.check_out_date, b.final_amount, b.status, b.billing_id
            FROM reservation r
            JOIN billing b ON b.reservation_id = r.reservation_id
            WHERE r.customer_id = ? AND b.status='Unpaid'
            ORDER BY r.check_in_date ASC
        """, (self.current_customer['customer_id'],), fetchall=True)
        
        if not rows:
            ctk.CTkLabel(frame, text="No unpaid reservations.").pack(pady=8)
        else:
            for r in rows:
                r_frame = ctk.CTkFrame(frame)
                r_frame.pack(fill='x', pady=4, padx=6)
                ctk.CTkLabel(r_frame, text=f"Reservation #{r['reservation_id']} | {r['check_in_date']} to {r['check_out_date']} | ₱{r['final_amount']:.2f}").pack(side='left', padx=6)
                
                def pay_reservation(res_id=r['reservation_id'], billing_id=r['billing_id'], amount=r['final_amount']):
                    method = simpledialog.askstring("Payment Method", "Enter payment method (cash, e-wallet, card):", parent=self)
                    if not method:
                        return
                    method = method.lower()
                    if method not in ('cash','e-wallet','card'):
                        messagebox.showerror("Invalid", "Method must be cash, e-wallet, or card")
                        return
                    # Save payment
                    from datetime import datetime
                    now = datetime.now().isoformat(sep=' ', timespec='seconds')
                    execute("INSERT INTO payment (billing_id, customer_id, payment_method, amount, payment_date) VALUES (?, ?, ?, ?, ?)",
                            (billing_id, self.current_customer['customer_id'], method, amount, now))
                    execute("UPDATE billing SET status='Paid' WHERE billing_id=?", (billing_id,))
                    messagebox.showinfo("Paid", f"Reservation #{res_id} paid via {method}.")
                    self.show_make_payment()
                
                ctk.CTkButton(r_frame, text="Pay", command=pay_reservation).pack(side='right', padx=6)
        
        ctk.CTkButton(frame, text="Back", command=self.show_admin_customer_dashboard).pack(pady=12) # NEW
        
    def show_receipts(self):
        if not self.current_customer:
            messagebox.showerror("Error", "No customer loaded.")
            return
        self.clear_container()
        frame = ctk.CTkScrollableFrame(self.container)
        frame.pack(pady=12, padx=12, expand=True, fill="both")
        
        ctk.CTkLabel(frame, text="My Receipts", font=("Helvetica", 22)).pack(pady=8)
        
        from db import query
        rows = query("""
            SELECT r.reservation_id, r.check_in_date, r.check_out_date, b.final_amount, p.payment_method, p.payment_date
            FROM reservation r
            JOIN billing b ON b.reservation_id = r.reservation_id
            JOIN payment p ON p.billing_id = b.billing_id
            WHERE r.customer_id = ? AND b.status='Paid'
            ORDER BY p.payment_date DESC
        """, (self.current_customer['customer_id'],), fetchall=True)
        
        if not rows:
            ctk.CTkLabel(frame, text="No receipts available.").pack(pady=8)
        else:
            for r in rows:
                txt = (f"Reservation #{r['reservation_id']} | {r['check_in_date']} to {r['check_out_date']}\n"
                    f"Amount: ₱{r['final_amount']:.2f} | Paid via: {r['payment_method']} | Date: {r['payment_date']}")
                r_frame = ctk.CTkFrame(frame)
                r_frame.pack(fill='x', pady=4, padx=6)
                ctk.CTkLabel(r_frame, text=txt, justify='left').pack(anchor='w', padx=6, pady=4)
        
        ctk.CTkButton(frame, text="Back", command=self.show_admin_customer_dashboard).pack(pady=12) # NEW

    # ------------------------- Reusable top-level -------------------------
    def open_text_window(self, title, content):
        def create():
            w = ctk.CTkToplevel(self)
            w.title(title)
            w.geometry("800x550")
            frame = ctk.CTkScrollableFrame(w, width=760, height=520)
            frame.pack(padx=12, pady=12, fill='both', expand=True)
            lbl = ctk.CTkLabel(frame, text=content, justify='left')
            lbl.pack(anchor='w')
            return w
        self.focus_or_create_window(title, create)


if __name__ == '__main__':
    app = MainApp()
    app.mainloop()
