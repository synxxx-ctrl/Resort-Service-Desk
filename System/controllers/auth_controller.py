# auth_controller.py
import tkinter as tk
from tkinter import messagebox, simpledialog
import customtkinter as ctk
from models import AdminModel  # adjust if your path is different

class AuthController:
    def __init__(self, app):
        """
        app = instance of MainApp (so we can access UI functions and main window)
        """
        self.app = app

    # ------------------------------------------------------------
    # OPEN ADMIN LOGIN WINDOW
    # ------------------------------------------------------------
    def open_admin_login(self):
        # Hide the main app window
        self.app.withdraw()

        # Create login popup
        login_win = ctk.CTkToplevel(self.app)
        login_win.title("Admin Login")
        login_win.geometry("320x260")
        login_win.resizable(False, False)
        login_win.grab_set()

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

        # -----------------------------------------
        # Attempt Login (inner function)
        # -----------------------------------------
        def attempt_login():
            username = username_var.get().strip()
            password = password_var.get().strip()

            if not username or not password:
                messagebox.showerror("Error", "Both fields are required.")
                return

            if AdminModel.check_login(username, password):
                login_win.destroy()
                self.app.deiconify()  # Show main window again
                # FIXED: Use the AdminDashboard instance
                self.app.admin_dashboard.show_admin_interface()
            else:
                messagebox.showerror("Login Failed", "Incorrect username or password.")

        # Support Enter key
        login_win.bind("<Return>", lambda event: attempt_login())

        # Proceed button
        ctk.CTkButton(login_win, text="Proceed", command=attempt_login).pack(pady=15)

        # Focus cursor
        username_entry.focus()

    # ------------------------------------------------------------
    # LOGOUT ADMIN
    # ------------------------------------------------------------
    def logout_admin(self):
        self.app.withdraw()  # hide main app

        # Destroy admin UI frame if it exists
        if hasattr(self.app.admin_dashboard, "container") and self.app.admin_dashboard.container.winfo_exists():
            self.app.admin_dashboard.clear_container()

        # Go back to login
        self.open_admin_login()

    # ------------------------------------------------------------
    # CHANGE ADMIN CREDENTIALS
    # ------------------------------------------------------------
    def change_admin_credentials(self):
        new_user = simpledialog.askstring("Change Admin Username", "New username:", parent=self.app)
        new_pass = simpledialog.askstring("Change Admin Password", "New password:", parent=self.app, show='*')

        if not new_user or not new_pass:
            messagebox.showerror("Error", "Both fields are required.")
            return

        from db import execute, query

        row = query("SELECT admin_id FROM admin LIMIT 1", fetchone=True)
        if row:
            execute(
                "UPDATE admin SET username=?, password=? WHERE admin_id=?",
                (new_user, new_pass, row["admin_id"])
            )
            messagebox.showinfo("Success", "Admin credentials updated.")
        else:
            messagebox.showerror("Error", "Admin record not found.")
