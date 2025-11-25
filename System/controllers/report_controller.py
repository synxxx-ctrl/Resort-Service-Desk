import customtkinter as ctk
from tkinter import messagebox, simpledialog
from datetime import datetime, date, timedelta
from db import query

class ReportController:
    def __init__(self, app):
        """
        Initialize the ReportController.
        :param app: Reference to the main application class.
        """
        self.app = app

    def generate_report(self):
        # Parent window is self.app
        win = ctk.CTkToplevel(self.app)
        win.title("Generate Report")
        win.geometry("360x320")
        
        # Make the report window modal/transient
        win.transient(self.app)
        win.grab_set()

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
                self.app.window_manager.open_text_window("Full Report", "No reservation data found.")
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

            self.app.window_manager.open_text_window("Full Report", txt)

        except Exception as e:
            messagebox.showerror("DB Error", f"Could not generate full report:\n{e}")

    def generate_daily_report_prompt(self):
        date_str = simpledialog.askstring(
            "Daily Report",
            "Enter date (YYYY-MM-DD):",
            parent=self.app
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
        start_str = simpledialog.askstring("Report Start Date", "Enter start date (YYYY-MM-DD):", parent=self.app)
        if not start_str:
            return
        end_str = simpledialog.askstring("Report End Date", "Enter end date (YYYY-MM-DD):", parent=self.app)
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
                self.app.window_manager.open_text_window(title, f"No reservations found between {start_date_str} and {end_date_str}.")
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
            self.app.window_manager.open_text_window(title, report_text)

        except Exception as e:
            messagebox.showerror("DB Error", f"Could not generate report:\n{e}")