import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, simpledialog
from db import execute, query 
from models import AdminModel 

class AuthController:
    def __init__(self, app):
        """
        Initialize the AuthController.
        :param app: Reference to the main application class (root window).
        """
        self.app = app

    def open_admin_login(self):
        """
        Opens the Admin Login popup. Hides the main window during login.
        """
        # Hide the main window (accessed via self.app)
        self.app.withdraw()

        # --- CREATE SMALL LOGIN WINDOW ---
        # Pass self.app as the master/parent
        login_win = ctk.CTkToplevel(self.app)
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
                self.app.deiconify()  # show main window
                
                # Call the main app's method to switch UI to Admin Interface
                # Ensure 'show_admin_interface' exists in your Main App or AdminDashboard controller
                if hasattr(self.app, 'show_admin_interface'):
                    self.app.show_admin_interface()
                elif hasattr(self.app, 'admin_dashboard'):
                    # If routed through the dashboard controller
                    self.app.admin_dashboard.show_admin_interface()
                else:
                    print("Error: show_admin_interface method not found on Main App.")
            else:
                messagebox.showerror("Login Failed", "Incorrect username or password.")

        # ENTER KEY SUPPORT
        login_win.bind("<Return>", lambda event: attempt_login())

        # Proceed button
        ctk.CTkButton(login_win, text="Proceed", command=attempt_login).pack(pady=15)

        # Focus cursor on username
        username_entry.focus()

    def logout_admin(self):
        """
        Logs out the admin, destroys the admin frame, and returns to login.
        """
        # Hide main window
        self.app.withdraw()

        # Destroy admin UI frame if it exists in the main app
        if hasattr(self.app, "admin_frame") and self.app.admin_frame is not None and self.app.admin_frame.winfo_exists():
            self.app.admin_frame.destroy()

        # Return to login window
        self.open_admin_login()

    def change_admin_credentials(self):
        """
        Dialog to update admin username/password in the database.
        """
        # Parent is self.app to ensure dialog appears over the main app
        new_user = simpledialog.askstring("Change Admin Username", "New username:", parent=self.app)
        new_pass = simpledialog.askstring("Change Admin Password", "New password:", parent=self.app, show='*')
        
        if not new_user or not new_pass:
            messagebox.showerror("Error", "Both fields are required.")
            return
        
        # Query DB
        row = query("SELECT admin_id FROM admin LIMIT 1", fetchone=True)
        
        if row:
            # fixed typos: single ? placeholders
            execute("UPDATE admin SET username=?, password=? WHERE admin_id=?", (new_user, new_pass, row['admin_id']))
            messagebox.showinfo("Success", "Admin credentials updated.")
        else:
            messagebox.showerror("Error", "Admin record not found.")