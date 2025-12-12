import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, date, timedelta
from db import query

class ReportController:
    def __init__(self, app):
        self.app = app

    def generate_report(self):
        # 1. Clear Main Container
        self.app.window_manager.clear_container()
        
        # 2. Main Frame
        frame = ctk.CTkFrame(self.app.container, fg_color="transparent")
        frame.pack(expand=True, fill="both", padx=20, pady=20)

        ctk.CTkLabel(frame, text="Report Center", font=("Arial", 28, "bold")).pack(pady=(20, 5))
        ctk.CTkLabel(frame, text="Select report type to generate", font=("Arial", 16), text_color="gray").pack(pady=(0, 40))

        # Base style for standard buttons
        btn_style = {"width": 300, "height": 50, "font": ("Arial", 15, "bold"), "fg_color": "#2c3e50", "hover_color": "#34495e"}

        ctk.CTkButton(frame, text="📅  Daily Report", command=lambda: self.open_date_input("daily"), **btn_style).pack(pady=10)
        ctk.CTkButton(frame, text="KW  Weekly Report (Last 7 Days)", command=self.generate_weekly_report, **btn_style).pack(pady=10)
        ctk.CTkButton(frame, text="📆  Monthly Report (Last 30 Days)", command=self.generate_monthly_report, **btn_style).pack(pady=10)
        ctk.CTkButton(frame, text="🔎  Custom Date Range", command=lambda: self.open_date_input("range"), **btn_style).pack(pady=10)
        
        ctk.CTkFrame(frame, height=2, width=250, fg_color="gray60").pack(pady=20)
        
        # Full History Button
        full_style = btn_style.copy()
        full_style.update({"fg_color": "#2980b9", "hover_color": "#3498db"})
        ctk.CTkButton(frame, text="📋  Full History Report", command=self.generate_full_report, **full_style).pack(pady=10)

    # ------------------------- INPUT VIEWS -------------------------

    def open_date_input(self, mode):
        self.app.window_manager.clear_container()
        
        frame = ctk.CTkFrame(self.app.container, fg_color="transparent")
        frame.pack(expand=True, fill="both", padx=20, pady=20)

        title_text = "Select Date" if mode == "daily" else "Select Date Range"
        ctk.CTkLabel(frame, text=title_text, font=("Arial", 24, "bold")).pack(pady=30)

        entries = {}
        input_frame = ctk.CTkFrame(frame, fg_color="transparent")
        input_frame.pack(pady=10)

        if mode == "daily":
            ctk.CTkLabel(input_frame, text="Date (YYYY-MM-DD):", font=("Arial", 14)).pack(pady=(10, 5))
            ent = ctk.CTkEntry(input_frame, width=250, font=("Arial", 14))
            ent.pack(pady=5)
            ent.insert(0, date.today().isoformat())
            entries['start'] = ent
        else:
            ctk.CTkLabel(input_frame, text="Start Date (YYYY-MM-DD):", font=("Arial", 14)).pack(pady=(10, 5))
            s_ent = ctk.CTkEntry(input_frame, width=250, font=("Arial", 14))
            s_ent.pack(pady=5)
            entries['start'] = s_ent
            
            ctk.CTkLabel(input_frame, text="End Date (YYYY-MM-DD):", font=("Arial", 14)).pack(pady=(15, 5))
            e_ent = ctk.CTkEntry(input_frame, width=250, font=("Arial", 14))
            e_ent.pack(pady=5)
            entries['end'] = e_ent

        def submit():
            try:
                s_str = entries['start'].get().strip()
                datetime.strptime(s_str, "%Y-%m-%d") # Validate format
                
                if mode == "daily":
                    start = f"{s_str} 00:00:00"
                    end = f"{s_str} 23:59:59"
                    self.generate_complex_report(start, end, f"Daily Report: {s_str}")
                else:
                    e_str = entries['end'].get().strip()
                    datetime.strptime(e_str, "%Y-%m-%d")
                    start = f"{s_str} 00:00:00"
                    end = f"{e_str} 23:59:59"
                    self.generate_complex_report(start, end, f"Range Report: {s_str} to {e_str}")
            except ValueError:
                messagebox.showerror("Format Error", "Invalid Date Format. Please use YYYY-MM-DD.")

        # Buttons
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(pady=40)
        ctk.CTkButton(btn_frame, text="Generate Report", command=submit, fg_color="#27ae60", width=160, height=40).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Back", command=self.generate_report, fg_color="transparent", border_width=1, width=120, height=40).pack(side="left", padx=10)

    # ------------------------- GENERATORS -------------------------
    
    def generate_full_report(self):
        self.generate_complex_report(None, None, "Full Resort History")

    def generate_weekly_report(self):
        end = datetime.now()
        start = end - timedelta(days=7)
        self.generate_complex_report(start.strftime("%Y-%m-%d 00:00:00"), end.strftime("%Y-%m-%d 23:59:59"), "Weekly Report (Last 7 Days)")

    def generate_monthly_report(self):
        end = datetime.now()
        start = end - timedelta(days=30)
        self.generate_complex_report(start.strftime("%Y-%m-%d 00:00:00"), end.strftime("%Y-%m-%d 23:59:59"), "Monthly Report (Last 30 Days)")

    # ------------------------- LOGIC & RENDER -------------------------

    def generate_complex_report(self, start_date, end_date, title):
        try:
            # 1. Build Query Filters
            if start_date and end_date:
                where_clause = "WHERE (REPLACE(r.check_in_date, 'T', ' ') <= ?) AND (REPLACE(r.check_out_date, 'T', ' ') >= ?)"
                params = (end_date, start_date)
                maint_where = "WHERE date_reported BETWEEN ? AND ?"
                maint_params = (start_date, end_date)
            else:
                where_clause = ""; params = (); maint_where = ""; maint_params = ()

            # 2. Fetch Data (Financials)
            fin_row = query(f"""
                SELECT COUNT(DISTINCT r.reservation_id) as total_res, 
                       SUM(b.final_amount) as total_revenue, 
                       SUM(b.amount_paid) as total_collected
                FROM reservation r 
                LEFT JOIN billing b ON r.reservation_id = b.reservation_id
                {where_clause}
            """, params, fetchone=True)
            
            t_res = fin_row['total_res'] or 0
            t_rev = fin_row['total_revenue'] or 0.0
            t_col = fin_row['total_collected'] or 0.0
            t_out = t_rev - t_col

            # 3. Fetch Services
            svc_rows = query(f"""
                SELECT s.service_name, SUM(rs.quantity) as usage_count
                FROM reservation_services rs
                JOIN reservation r ON rs.reservation_id = r.reservation_id
                JOIN service s ON rs.service_id = s.service_id
                {where_clause} 
                GROUP BY s.service_name ORDER BY usage_count DESC
            """, params, fetchall=True)

            # 4. Fetch Maintenance
            maint_rows = query(f"SELECT COUNT(*) as issue_count, status FROM maintenance_logs {maint_where} GROUP BY status", maint_params, fetchall=True)
            
            # 5. Fetch Details
            res_rows = query(f"""
                SELECT r.reservation_id, c.full_name, REPLACE(r.check_in_date, 'T', ' ') as check_in_display, 
                       r.status, b.final_amount, b.amount_paid
                FROM reservation r JOIN customer c ON r.customer_id = c.customer_id
                LEFT JOIN billing b ON r.reservation_id = b.reservation_id
                {where_clause} ORDER BY r.check_in_date DESC
            """, params, fetchall=True)

            self.show_report_view(title, t_res, t_rev, t_col, t_out, svc_rows, maint_rows, res_rows)

        except Exception as e:
            messagebox.showerror("Error", f"Report failed: {e}")

    def show_report_view(self, title, t_res, t_rev, t_col, t_out, svc_data, maint_data, res_data):
        self.app.window_manager.clear_container()
        
        # Scrollable Container
        scroll = ctk.CTkScrollableFrame(self.app.container)
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        head = ctk.CTkFrame(scroll, fg_color="transparent")
        head.pack(fill="x", pady=(10, 20))
        ctk.CTkLabel(head, text=title, font=("Arial", 26, "bold")).pack(side="left")
        ctk.CTkButton(head, text="Back to Menu", command=self.generate_report, width=120).pack(side="right")
        ctk.CTkLabel(scroll, text=f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", text_color="gray").pack(anchor="w", pady=(0, 20))

        # --- CARDS ---
        cards = ctk.CTkFrame(scroll, fg_color="transparent")
        cards.pack(fill="x", pady=10)
        cards.columnconfigure((0,1,2), weight=1)

        self.create_stat_card(cards, "Revenue", f"₱{t_rev:,.2f}", "#2980b9", 0, 0)
        self.create_stat_card(cards, "Collected", f"₱{t_col:,.2f}", "#27ae60", 0, 1)
        self.create_stat_card(cards, "Outstanding", f"₱{t_out:,.2f}", "#c0392b", 0, 2)

        # --- SPLIT VIEW ---
        split = ctk.CTkFrame(scroll, fg_color="transparent")
        split.pack(fill="x", pady=20)
        split.columnconfigure((0, 1), weight=1)

        # Top Services
        svc_f = ctk.CTkFrame(split, corner_radius=10)
        svc_f.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        ctk.CTkLabel(svc_f, text="Top Services / Amenities", font=("Arial", 16, "bold")).pack(pady=10)
        if svc_data:
            for s in svc_data[:8]: # Limit to top 8
                row = ctk.CTkFrame(svc_f, fg_color="transparent")
                row.pack(fill="x", padx=15, pady=2)
                ctk.CTkLabel(row, text=s['service_name'], anchor="w").pack(side="left")
                ctk.CTkLabel(row, text=f"x{s['usage_count']}", font=("Arial", 12, "bold")).pack(side="right")
        else:
            ctk.CTkLabel(svc_f, text="No data.", text_color="gray").pack(pady=10)

        # Maintenance
        maint_f = ctk.CTkFrame(split, corner_radius=10)
        maint_f.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        ctk.CTkLabel(maint_f, text="Maintenance Status", font=("Arial", 16, "bold")).pack(pady=10)
        m_count = sum(m['issue_count'] for m in maint_data) if maint_data else 0
        ctk.CTkLabel(maint_f, text=f"{m_count} Issues", font=("Arial", 28, "bold"), text_color="#e67e22").pack(pady=5)
        if maint_data:
            for m in maint_data:
                ctk.CTkLabel(maint_f, text=f"{m['status']}: {m['issue_count']}").pack()
        else:
            ctk.CTkLabel(maint_f, text="All Clear", text_color="green").pack(pady=5)

        # --- TABLE ---
        ctk.CTkLabel(scroll, text=f"Reservations List ({t_res} Total)", font=("Arial", 18, "bold")).pack(anchor="w", pady=(20, 10))
        
        # Headers
        h_frame = ctk.CTkFrame(scroll, fg_color="gray30", height=35)
        h_frame.pack(fill="x")
        cols = [("ID", 50), ("Customer", 200), ("Status", 100), ("Check-In", 120), ("Total", 100)]
        for txt, w in cols:
            f = ctk.CTkFrame(h_frame, width=w, fg_color="transparent")
            f.pack(side="left", fill="y", expand=True)
            ctk.CTkLabel(f, text=txt, font=("Arial", 12, "bold")).pack()
            
        if not res_data:
            ctk.CTkLabel(scroll, text="No records found.", text_color="gray").pack(pady=20)
        else:
            for r in res_data:
                row = ctk.CTkFrame(scroll, fg_color=("gray85", "gray25"), height=35)
                row.pack(fill="x", pady=2)
                
                c_in = r['check_in_display'].split(' ')[0] if r['check_in_display'] else ""
                vals = [f"#{r['reservation_id']}", r['full_name'], r['status'], c_in, f"₱{r['final_amount'] or 0:,.2f}"]
                
                for i, val in enumerate(vals):
                    f = ctk.CTkFrame(row, width=cols[i][1], fg_color="transparent")
                    f.pack(side="left", fill="y", expand=True)
                    ctk.CTkLabel(f, text=val).pack()

    def create_stat_card(self, parent, title, value, color, r, c):
        card = ctk.CTkFrame(parent, corner_radius=10, fg_color=color)
        card.grid(row=r, column=c, padx=10, sticky="nsew")
        ctk.CTkLabel(card, text=title, text_color="white", font=("Arial", 14)).pack(pady=(15,0))
        ctk.CTkLabel(card, text=value, text_color="white", font=("Arial", 24, "bold")).pack(pady=(5,15))