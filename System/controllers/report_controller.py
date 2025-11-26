import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, date, timedelta
from db import query

class ReportController:
    def __init__(self, app):
        self.app = app

    def generate_report(self):
        # --- MAIN MENU WINDOW ---
        win = ctk.CTkToplevel(self.app)
        win.title("Generate Report")
        win.geometry("400x450")
        win.transient(self.app)
        win.grab_set()

        ctk.CTkLabel(win, text="Report Center", font=("Arial", 22, "bold")).pack(pady=(20, 5))
        ctk.CTkLabel(win, text="Select report type to generate", font=("Arial", 14), text_color="gray").pack(pady=(0, 20))

        # Base style for standard buttons
        btn_style = {"width": 300, "height": 45, "font": ("Arial", 14, "bold"), "fg_color": "#2c3e50", "hover_color": "#34495e"}

        ctk.CTkButton(win, text="📅  Daily Report", command=lambda: (win.destroy(), self.open_date_input("daily")), **btn_style).pack(pady=8)
        ctk.CTkButton(win, text="KW  Weekly Report (Last 7 Days)", command=lambda: (win.destroy(), self.generate_weekly_report()), **btn_style).pack(pady=8)
        ctk.CTkButton(win, text="📆  Monthly Report (Last 30 Days)", command=lambda: (win.destroy(), self.generate_monthly_report()), **btn_style).pack(pady=8)
        ctk.CTkButton(win, text="🔎  Custom Date Range", command=lambda: (win.destroy(), self.open_date_input("range")), **btn_style).pack(pady=8)
        
        ctk.CTkFrame(win, height=2, width=250, fg_color="gray").pack(pady=15)
        
        # Specific style for this button
        full_style = btn_style.copy()
        full_style.update({"fg_color": "#2980b9", "hover_color": "#3498db"})
        
        ctk.CTkButton(win, text="📋  Full History Report", command=lambda: (win.destroy(), self.generate_full_report()), 
                      **full_style).pack(pady=8)

        ctk.CTkButton(win, text="Cancel", command=win.destroy, fg_color="transparent", border_width=1, text_color=("gray10", "gray90"), width=200).pack(pady=10)

    # ------------------------- CUSTOM INPUT WINDOWS -------------------------

    def open_date_input(self, mode):
        input_win = ctk.CTkToplevel(self.app)
        input_win.title("Select Date")
        input_win.geometry("350x350") # Slightly taller for buttons
        input_win.transient(self.app)
        input_win.grab_set()

        title_text = "Select Date" if mode == "daily" else "Select Date Range"
        ctk.CTkLabel(input_win, text=title_text, font=("Arial", 18, "bold")).pack(pady=20)

        entries = {}

        if mode == "daily":
            ctk.CTkLabel(input_win, text="Date (YYYY-MM-DD):").pack(pady=(10, 5))
            ent = ctk.CTkEntry(input_win, width=200, placeholder_text="2023-12-25")
            ent.pack(pady=5)
            entries['start'] = ent
        else:
            ctk.CTkLabel(input_win, text="Start Date (YYYY-MM-DD):").pack(pady=(5, 2))
            s_ent = ctk.CTkEntry(input_win, width=200)
            s_ent.pack(pady=5)
            entries['start'] = s_ent
            
            ctk.CTkLabel(input_win, text="End Date (YYYY-MM-DD):").pack(pady=(5, 2))
            e_ent = ctk.CTkEntry(input_win, width=200)
            e_ent.pack(pady=5)
            entries['end'] = e_ent

        def submit():
            try:
                s_str = entries['start'].get().strip()
                datetime.strptime(s_str, "%Y-%m-%d") # Validate
                
                if mode == "daily":
                    start = f"{s_str} 00:00:00"
                    end = f"{s_str} 23:59:59"
                    input_win.destroy()
                    self.generate_complex_report(start, end, f"Daily Report: {s_str}")
                else:
                    e_str = entries['end'].get().strip()
                    datetime.strptime(e_str, "%Y-%m-%d") # Validate
                    
                    start = f"{s_str} 00:00:00"
                    end = f"{e_str} 23:59:59"
                    input_win.destroy()
                    self.generate_complex_report(start, end, f"Range Report: {s_str} to {e_str}")
            except ValueError:
                messagebox.showerror("Format Error", "Invalid Date Format.\nPlease use YYYY-MM-DD.", parent=input_win)

        # --- BUTTONS FRAME ---
        btn_frame = ctk.CTkFrame(input_win, fg_color="transparent")
        btn_frame.pack(pady=30)

        ctk.CTkButton(btn_frame, text="Generate Report", command=submit, fg_color="#27ae60", width=140).pack(side="left", padx=10)
        
        # --- ADDED BACK BUTTON ---
        ctk.CTkButton(btn_frame, text="Back", command=input_win.destroy, fg_color="transparent", border_width=1, text_color=("gray10", "gray90"), width=100).pack(side="left", padx=10)

    # ------------------------- PRESET REPORTS -------------------------
    
    def generate_full_report(self):
        self.generate_complex_report(None, None, "Full Resort History")

    def generate_weekly_report(self):
        end = datetime.now()
        start = end - timedelta(days=7)
        self.generate_complex_report(start.isoformat(), end.isoformat(), "Weekly Report (Last 7 Days)")

    def generate_monthly_report(self):
        end = datetime.now()
        start = end - timedelta(days=30)
        self.generate_complex_report(start.isoformat(), end.isoformat(), "Monthly Report (Last 30 Days)")

    # ------------------------- CORE LOGIC & UI RENDERING -------------------------

    def generate_complex_report(self, start_date, end_date, title):
        try:
            # 1. FILTER LOGIC
            if start_date and end_date:
                where_clause = "WHERE (r.check_in_date BETWEEN ? AND ?) OR (r.check_out_date BETWEEN ? AND ?)"
                params = (start_date, end_date, start_date, end_date)
                maint_where = "WHERE date_reported BETWEEN ? AND ?"
                maint_params = (start_date, end_date)
            else:
                where_clause = ""
                params = ()
                maint_where = ""
                maint_params = ()

            # 2. FETCH DATA
            
            # Financials
            fin_row = query(f"""
                SELECT COUNT(r.reservation_id) as total_res, SUM(b.final_amount) as total_revenue, SUM(b.amount_paid) as total_collected
                FROM reservation r LEFT JOIN billing b ON r.reservation_id = b.reservation_id
                {where_clause}
            """, params, fetchone=True)
            
            total_res = fin_row['total_res'] or 0
            total_rev = fin_row['total_revenue'] or 0.0
            total_col = fin_row['total_collected'] or 0.0
            outstanding = total_rev - total_col

            # Service Usage
            svc_rows = query(f"""
                SELECT s.service_name, SUM(rs.quantity) as usage_count
                FROM reservation_services rs
                JOIN reservation r ON rs.reservation_id = r.reservation_id
                JOIN service s ON rs.service_id = s.service_id
                {where_clause} GROUP BY s.service_name ORDER BY usage_count DESC
            """, params, fetchall=True)

            # Maintenance
            maint_rows = query(f"""
                SELECT COUNT(*) as issue_count, status FROM maintenance_logs 
                {maint_where} GROUP BY status
            """, maint_params, fetchall=True)
            
            # Detailed List
            res_rows = query(f"""
                SELECT r.reservation_id, c.full_name, r.check_in_date, r.check_out_date, r.status, b.final_amount, b.amount_paid
                FROM reservation r JOIN customer c ON r.customer_id = c.customer_id
                LEFT JOIN billing b ON r.reservation_id = b.reservation_id
                {where_clause} ORDER BY r.check_in_date DESC
            """, params, fetchall=True)

            # 3. RENDER THE FANCY UI
            self.show_report_window(title, total_res, total_rev, total_col, outstanding, svc_rows, maint_rows, res_rows)

        except Exception as e:
            messagebox.showerror("Report Error", f"Failed to generate:\n{e}", parent=self.app)

    def show_report_window(self, title, t_res, t_rev, t_col, t_out, svc_data, maint_data, res_data):
        rep_win = ctk.CTkToplevel(self.app)
        rep_win.title(title)
        rep_win.geometry("900x700")
        rep_win.transient(self.app)
        
        # Main Scrollable Container
        main_scroll = ctk.CTkScrollableFrame(rep_win)
        main_scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # Header
        ctk.CTkLabel(main_scroll, text=title, font=("Arial", 24, "bold")).pack(pady=15)
        ctk.CTkLabel(main_scroll, text=f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", font=("Arial", 12), text_color="gray").pack()

        # --- SECTION 1: FINANCIAL CARDS ---
        fin_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
        fin_frame.pack(fill="x", pady=20, padx=10)
        fin_frame.columnconfigure((0,1,2), weight=1)

        self.create_stat_card(fin_frame, "Total Revenue", f"₱{t_rev:,.2f}", "#2980b9", 0, 0)
        self.create_stat_card(fin_frame, "Cash Collected", f"₱{t_col:,.2f}", "#27ae60", 0, 1)
        self.create_stat_card(fin_frame, "Outstanding", f"₱{t_out:,.2f}", "#c0392b", 0, 2)
        
        ctk.CTkLabel(main_scroll, text=f"Total Reservations: {t_res}", font=("Arial", 14, "bold")).pack(pady=5)

        # --- SECTION 2: SPLIT VIEW (SERVICES & MAINTENANCE) ---
        split_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
        split_frame.pack(fill="x", pady=10, padx=10)
        split_frame.columnconfigure((0, 1), weight=1)

        # Services Column
        svc_card = ctk.CTkFrame(split_frame, corner_radius=10)
        svc_card.grid(row=0, column=0, sticky="nsew", padx=5)
        ctk.CTkLabel(svc_card, text="Top Amenities Used", font=("Arial", 16, "bold")).pack(pady=10)
        if svc_data:
            for s in svc_data:
                row = ctk.CTkFrame(svc_card, fg_color="transparent")
                row.pack(fill="x", padx=15, pady=2)
                ctk.CTkLabel(row, text=s['service_name'], anchor="w").pack(side="left")
                ctk.CTkLabel(row, text=f"x{s['usage_count']}", font=("Arial", 12, "bold")).pack(side="right")
        else:
            ctk.CTkLabel(svc_card, text="No data available", text_color="gray").pack(pady=10)
        ctk.CTkLabel(svc_card, text="").pack(pady=5) # Spacer

        # Maintenance Column
        maint_card = ctk.CTkFrame(split_frame, corner_radius=10)
        maint_card.grid(row=0, column=1, sticky="nsew", padx=5)
        ctk.CTkLabel(maint_card, text="Maintenance Summary", font=("Arial", 16, "bold")).pack(pady=10)
        
        total_issues = sum(m['issue_count'] for m in maint_data) if maint_data else 0
        ctk.CTkLabel(maint_card, text=f"Total Reports: {total_issues}", font=("Arial", 24, "bold"), text_color="#e67e22").pack(pady=5)
        
        if maint_data:
            for m in maint_data:
                ctk.CTkLabel(maint_card, text=f"{m['status']}: {m['issue_count']}", font=("Arial", 13)).pack()
        else:
            ctk.CTkLabel(maint_card, text="No issues reported", text_color="gray").pack(pady=5)
        
        ctk.CTkLabel(maint_card, text="").pack(pady=5)

        # --- SECTION 3: DETAILED TABLE ---
        ctk.CTkLabel(main_scroll, text="Reservation Logs", font=("Arial", 18, "bold")).pack(pady=(25, 10), anchor="w", padx=15)
        
        # Table Header
        header = ctk.CTkFrame(main_scroll, height=35, fg_color="gray30")
        header.pack(fill="x", padx=10)
        headers = [("ID", 50), ("Customer", 200), ("Status", 100), ("Check-In", 100), ("Total", 100), ("Paid", 100)]
        for txt, w in headers:
            f = ctk.CTkFrame(header, width=w, fg_color="transparent")
            f.pack(side="left", fill="y", expand=True)
            ctk.CTkLabel(f, text=txt, font=("Arial", 12, "bold")).pack()

        # Rows
        if not res_data:
            ctk.CTkLabel(main_scroll, text="No records found for this period.", font=("Arial", 14)).pack(pady=20)
        else:
            for r in res_data:
                row = ctk.CTkFrame(main_scroll, height=35, fg_color=("gray85", "gray25"))
                row.pack(fill="x", padx=10, pady=2)
                
                vals = [
                    f"#{r['reservation_id']}", 
                    r['full_name'], 
                    r['status'], 
                    r['check_in_date'].split('T')[0], 
                    f"₱{r['final_amount'] or 0:,.2f}", 
                    f"₱{r['amount_paid'] or 0:,.2f}"
                ]
                
                for i, val in enumerate(vals):
                    w = headers[i][1]
                    f = ctk.CTkFrame(row, width=w, fg_color="transparent")
                    f.pack(side="left", fill="y", expand=True)
                    ctk.CTkLabel(f, text=val, font=("Arial", 12)).pack()

        ctk.CTkButton(main_scroll, text="Close Report", command=rep_win.destroy, width=200, fg_color="#c0392b").pack(pady=30)

    def create_stat_card(self, parent, title, value, color, r, c):
        card = ctk.CTkFrame(parent, corner_radius=10, fg_color=color)
        card.grid(row=r, column=c, padx=10, sticky="nsew")
        ctk.CTkLabel(card, text=title, text_color="white", font=("Arial", 14, "bold")).pack(pady=(15,0))
        ctk.CTkLabel(card, text=value, text_color="white", font=("Arial", 22, "bold")).pack(pady=(5,15))