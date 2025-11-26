import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
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
        login_win.title("Resort Service Desk")
        login_win.geometry("320x260")
        login_win.resizable(False, False)
        login_win.grab_set()   # Prevent clicking anywhere else

        # Center the window
        login_win.update_idletasks()
        try:
            x = (login_win.winfo_screenwidth() // 2) - (320 // 2)
            y = (login_win.winfo_screenheight() // 2) - (260 // 2)
            login_win.geometry(f"320x260+{x}+{y}")
        except:
            pass

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
        Opens a custom window to update admin username/password.
        """
        # Create a new top-level window
        win = ctk.CTkToplevel(self.app)
        win.title("Change Admin Credentials")
        win.geometry("350x300")
        win.resizable(False, False)
        win.transient(self.app)  # Keep on top of main window
        win.grab_set()           # Modal dialog behavior

        # Center the window
        win.update_idletasks()
        try:
            x = (win.winfo_screenwidth() // 2) - (350 // 2)
            y = (win.winfo_screenheight() // 2) - (300 // 2)
            win.geometry(f"+{x}+{y}")
        except:
            pass

        ctk.CTkLabel(win, text="Update Credentials", font=("Helvetica", 18, "bold")).pack(pady=15)

        # New Username
        ctk.CTkLabel(win, text="New Username:").pack(pady=(5, 0))
        user_entry = ctk.CTkEntry(win, width=220)
        user_entry.pack(pady=5)

        # New Password
        ctk.CTkLabel(win, text="New Password:").pack(pady=(5, 0))
        pass_entry = ctk.CTkEntry(win, width=220, show="*")
        pass_entry.pack(pady=5)

        def save_credentials():
            new_user = user_entry.get().strip()
            new_pass = pass_entry.get().strip()

            if not new_user or not new_pass:
                messagebox.showerror("Error", "Both username and password are required.", parent=win)
                return

            # Query to find the admin to update
            row = query("SELECT admin_id FROM admin LIMIT 1", fetchone=True)
            
            if row:
                try:
                    # Use AdminModel logic or direct execution
                    AdminModel.change_credentials(row['admin_id'], new_user, new_pass)
                    messagebox.showinfo("Success", "Admin credentials updated successfully.", parent=win)
                    win.destroy()
                except Exception as e:
                    messagebox.showerror("Database Error", f"Failed to update: {e}", parent=win)
            else:
                messagebox.showerror("Error", "Admin record not found.", parent=win)

        # Buttons
        ctk.CTkButton(win, text="Save Changes", command=save_credentials, fg_color="green").pack(pady=15)
        ctk.CTkButton(win, text="Cancel", command=win.destroy, fg_color="transparent", border_width=1, text_color=("gray10", "gray90")).pack(pady=5)