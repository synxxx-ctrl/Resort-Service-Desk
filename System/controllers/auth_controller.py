import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from db import execute, query 
from models import AdminModel 

class AuthController:
    def __init__(self, app):
        self.app = app

    def open_admin_login(self):
        # ... (Keep existing login logic intact for popup) ...
        self.app.withdraw()
        login_win = ctk.CTkToplevel(self.app)
        login_win.title("Resort Service Desk")
        login_win.geometry("320x260")
        login_win.resizable(False, False)
        login_win.grab_set()

        try:
            x = (login_win.winfo_screenwidth() // 2) - (320 // 2)
            y = (login_win.winfo_screenheight() // 2) - (260 // 2)
            login_win.geometry(f"320x260+{x}+{y}")
        except: pass

        ctk.CTkLabel(login_win, text="Admin Login", font=("Helvetica", 20)).pack(pady=10)
        ctk.CTkLabel(login_win, text="Username:").pack()
        username_var = tk.StringVar()
        ctk.CTkEntry(login_win, width=200, textvariable=username_var).pack(pady=5)
        ctk.CTkLabel(login_win, text="Password:").pack()
        password_var = tk.StringVar()
        pass_ent = ctk.CTkEntry(login_win, width=200, show="*", textvariable=password_var)
        pass_ent.pack(pady=5)

        def attempt_login():
            user = username_var.get().strip()
            pw = password_var.get().strip()
            if AdminModel.check_login(user, pw):
                login_win.destroy()
                self.app.deiconify()
                if hasattr(self.app, 'show_admin_interface'): self.app.show_admin_interface()
                elif hasattr(self.app, 'admin_dashboard'): self.app.admin_dashboard.show_admin_interface()
            else:
                messagebox.showerror("Failed", "Incorrect credentials.")
        
        login_win.bind("<Return>", lambda e: attempt_login())
        ctk.CTkButton(login_win, text="Login", command=attempt_login).pack(pady=15)
        pass_ent.focus()

    def logout_admin(self):
        self.app.withdraw()
        if hasattr(self.app, 'container'):
             for w in self.app.container.winfo_children(): w.destroy()
        self.open_admin_login()

    # --- UPDATED: With Confirm Password Logic ---
    def change_admin_credentials(self):
        self.app.window_manager.clear_container()
        
        frame = ctk.CTkFrame(self.app.container, fg_color="transparent")
        frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Increased height for extra field
        box = ctk.CTkFrame(frame, corner_radius=10, width=400)
        box.place(relx=0.5, rely=0.45, anchor="center")
        
        ctk.CTkLabel(box, text="Update Admin Credentials", font=("Arial", 22, "bold")).pack(pady=(30, 20), padx=40)

        ctk.CTkLabel(box, text="New Username:").pack(anchor="w", padx=40)
        user_entry = ctk.CTkEntry(box, width=300)
        user_entry.pack(pady=(5, 15), padx=40)

        ctk.CTkLabel(box, text="New Password:").pack(anchor="w", padx=40)
        pass_entry = ctk.CTkEntry(box, width=300, show="*")
        pass_entry.pack(pady=(5, 15), padx=40)

        # --- NEW FIELD ---
        ctk.CTkLabel(box, text="Confirm Password:").pack(anchor="w", padx=40)
        confirm_pass_entry = ctk.CTkEntry(box, width=300, show="*")
        confirm_pass_entry.pack(pady=(5, 20), padx=40)

        def save_credentials():
            new_user = user_entry.get().strip()
            new_pass = pass_entry.get().strip()
            conf_pass = confirm_pass_entry.get().strip()

            if not new_user or not new_pass or not conf_pass:
                messagebox.showerror("Error", "All fields are required.")
                return
            
            # --- CONFIRMATION CHECK ---
            if new_pass != conf_pass:
                messagebox.showerror("Error", "Passwords do not match.")
                return

            row = query("SELECT admin_id FROM admin LIMIT 1", fetchone=True)
            if row:
                try:
                    AdminModel.change_credentials(row['admin_id'], new_user, new_pass)
                    messagebox.showinfo("Success", "Credentials updated successfully.")
                    # Clear fields
                    user_entry.delete(0, 'end')
                    pass_entry.delete(0, 'end')
                    confirm_pass_entry.delete(0, 'end')
                except Exception as e:
                    messagebox.showerror("Error", f"Failed: {e}")
        
        ctk.CTkButton(box, text="Save Changes", command=save_credentials, width=300, height=40, fg_color="green").pack(pady=(0, 10), padx=40)
        ctk.CTkButton(box, text="Cancel", command=self.app.admin_dashboard.show_default_view, width=300, height=40, fg_color="transparent", border_width=1).pack(pady=(0, 30), padx=40)