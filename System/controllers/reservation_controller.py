import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from datetime import datetime, date, timedelta
from db import get_conn, query
from models import RoomModel, ResortModel, AmenityModel

try:
    from tkcalendar import DateEntry
    TKCALENDAR_AVAILABLE = True
except ImportError:
    TKCALENDAR_AVAILABLE = False

class ReservationController:
    def __init__(self, app):
        self.app = app
        
        self.room_id_var = None
        self.room_selection_display_var = None
        self.room_capacity = 0
        self.room_capacity_label = None
        self.cart_items_container = None
        self.total_label = None
        self.checkin_widget = None
        self.checkout_widget = None
        self.type_var = None
        self.guest_vars = {}
        
        # Time Vars for Day Tour
        self.start_h = None
        self.start_m = None
        self.start_p = None
        self.end_h = None
        self.end_m = None
        self.end_p = None

    def show_reservations(self):
        self.app.window_manager.clear_container()
        frame = ctk.CTkScrollableFrame(self.app.container, corner_radius=10)
        frame.pack(pady=15, padx=15, expand=True, fill="both")
        ctk.CTkLabel(frame, text="All Reservations", font=("Arial", 26, "bold")).pack(pady=15)
        
        rows = query("""
            SELECT r.*, c.full_name, rm.room_number, rm.type as room_type, b.final_amount, b.amount_paid, b.status as payment_status
            FROM reservation r
            JOIN customer c ON r.customer_id = c.customer_id
            LEFT JOIN room rm ON r.room_id = rm.room_id
            LEFT JOIN billing b ON r.reservation_id = b.reservation_id
            ORDER BY r.check_in_date DESC
        """, fetchall=True)
        
        if not rows:
            ctk.CTkLabel(frame, text="No reservations found.", font=("Arial", 16)).pack(pady=20)
        else:
            for r in rows:
                card = ctk.CTkFrame(frame, fg_color=("gray85", "gray25"), corner_radius=8)
                card.pack(fill='x', pady=8, padx=10)
                
                header_frame = ctk.CTkFrame(card, fg_color="transparent")
                header_frame.pack(fill='x', padx=15, pady=(10, 5))
                status_color = "#27ae60" if r['status'] == 'Checked-in' else ("#c0392b" if r['status'] == 'Cancelled' else "#f39c12")
                
                ctk.CTkLabel(header_frame, text=f"Res #{r['reservation_id']} | {r['full_name']}", font=("Arial", 18, "bold")).pack(side="left")
                ctk.CTkLabel(header_frame, text=f"[{r['status']}]", text_color=status_color, font=("Arial", 16, "bold")).pack(side="right")

                cin = r['check_in_date'].replace('T', ' ')
                cout = r['check_out_date'].replace('T', ' ')
                
                details = (f"Unit: {r['room_number'] or 'Day Tour/None'}\n"
                           f"Date: {cin} -> {cout}\n"
                           f"Pax: Adult({r['count_adults']}), Teen/Kid({r['count_teens']}), Toddler({r['count_kids']})")
                
                ctk.CTkLabel(card, text=details, justify="left", font=("Arial", 14)).pack(anchor="w", padx=15, pady=5)

        ctk.CTkButton(frame, text="Back", command=self.app.admin_dashboard.show_admin_interface).pack(pady=20)

    # --- MAIN RESERVATION UI ---
    def show_make_reservation(self):
        self.app.cart = []
        self.app.window_manager.clear_container()
        
        frame = ctk.CTkFrame(self.app.container)
        frame.pack(pady=12, padx=12, expand=True, fill="both")
        
        left = ctk.CTkFrame(frame); left.pack(side="left", expand=True, fill="both", padx=12, pady=12)
        right = ctk.CTkFrame(frame, width=350); right.pack(side="right", fill="y", padx=12, pady=12)

        ctk.CTkLabel(left, text="Create Reservation", font=("Arial", 22, "bold")).pack(pady=10)
        
        # 1. Type
        self.type_var = tk.StringVar(value="Overnight Stay")
        
        def on_type_change(value):
            if value == "Day Tour (Future/Same Day)":
                if TKCALENDAR_AVAILABLE: self.checkout_widget.pack_forget() 
                self.checkout_lbl.pack_forget()
                self.time_frame.pack(in_=schedule_container, pady=5)
            else:
                if TKCALENDAR_AVAILABLE: self.checkout_widget.pack(side="left", padx=5)
                self.checkout_lbl.pack(side="left", padx=5)
                self.time_frame.pack_forget()
            self.update_cart_preview()

        seg = ctk.CTkSegmentedButton(left, values=["Overnight Stay", "Day Tour (Future/Same Day)"], variable=self.type_var, command=on_type_change)
        seg.pack(pady=10); seg.set("Overnight Stay")

        # 2. Schedule
        schedule_container = ctk.CTkFrame(left, fg_color="transparent")
        schedule_container.pack(pady=5, fill="x")

        date_frame = ctk.CTkFrame(schedule_container, fg_color="transparent")
        date_frame.pack(pady=5)
        
        ctk.CTkLabel(date_frame, text="Check-in / Date:").pack(side="left", padx=5)
        if TKCALENDAR_AVAILABLE:
            self.checkin_widget = DateEntry(date_frame, width=12)
            self.checkin_widget.pack(side="left", padx=5)
            
            self.checkout_lbl = ctk.CTkLabel(date_frame, text="Check-out:")
            self.checkout_lbl.pack(side="left", padx=5)
            self.checkout_widget = DateEntry(date_frame, width=12)
            self.checkout_widget.pack(side="left", padx=5)
        else:
            self.checkin_widget = ctk.CTkEntry(date_frame, width=100, placeholder_text="YYYY-MM-DD")
            self.checkin_widget.pack(side="left", padx=5)
            self.checkout_lbl = ctk.CTkLabel(date_frame, text="Check-out:")
            self.checkout_lbl.pack(side="left", padx=5)
            self.checkout_widget = ctk.CTkEntry(date_frame, width=100, placeholder_text="YYYY-MM-DD")
            self.checkout_widget.pack(side="left", padx=5)

        self.time_frame = ctk.CTkFrame(schedule_container, fg_color="transparent")
        t_inner = ctk.CTkFrame(self.time_frame, fg_color="transparent"); t_inner.pack()
        hours = [str(i) for i in range(1, 13)]
        ctk.CTkLabel(t_inner, text="Time:").grid(row=0, column=0, padx=5)
        self.start_h = ctk.CTkOptionMenu(t_inner, values=hours, width=60); self.start_h.grid(row=0, column=1)
        self.start_m = ctk.CTkOptionMenu(t_inner, values=["00","15","30","45"], width=60); self.start_m.grid(row=0, column=2)
        self.start_p = ctk.CTkOptionMenu(t_inner, values=["AM","PM"], width=60); self.start_p.grid(row=0, column=3, padx=5); self.start_p.set("AM")
        ctk.CTkLabel(t_inner, text="to").grid(row=0, column=4, padx=5)
        self.end_h = ctk.CTkOptionMenu(t_inner, values=hours, width=60); self.end_h.grid(row=0, column=5)
        self.end_m = ctk.CTkOptionMenu(t_inner, values=["00","15","30","45"], width=60); self.end_m.grid(row=0, column=6)
        self.end_p = ctk.CTkOptionMenu(t_inner, values=["AM","PM"], width=60); self.end_p.grid(row=0, column=7, padx=5); self.end_p.set("PM")

        # 3. Guests
        gf = ctk.CTkFrame(left)
        gf.pack(pady=10, fill='x', padx=10)
        ctk.CTkLabel(gf, text="Guest Count (For Entrance Fees)", font=("Arial", 14, "bold")).pack(pady=5)
        grid_f = ctk.CTkFrame(gf, fg_color="transparent"); grid_f.pack()
        
        labels = ["Adults", "Kids (6+) / Teens", "Toddlers (<=5)", "Seniors (20% Off)", "PWD (20% Off)"]
        keys = ["adult", "teen", "kid", "senior", "pwd"]
        
        self.guest_vars = {}
        for i, (txt, key) in enumerate(zip(labels, keys)):
            ctk.CTkLabel(grid_f, text=txt).grid(row=0, column=i, padx=5)
            v = tk.StringVar(value="0" if key != "adult" else "1")
            self.guest_vars[key] = v
            ctk.CTkEntry(grid_f, width=50, textvariable=v).grid(row=1, column=i, padx=5, pady=5)

        # 4. Unit Selection
        ctk.CTkLabel(left, text="Select Unit (Optional for Day Tour):").pack(pady=(15, 5))
        self.room_id_var = tk.StringVar(value="0")
        self.room_selection_display_var = tk.StringVar(value="No Unit Selected")
        self.room_capacity_label = ctk.CTkLabel(left, text="Capacity: N/A", text_color="gray")
        ctk.CTkLabel(left, textvariable=self.room_selection_display_var, font=("Arial", 14, "bold"), text_color="#e67e22").pack()
        self.room_capacity_label.pack()

        btn_row = ctk.CTkFrame(left, fg_color="transparent")
        btn_row.pack(pady=5)
        ctk.CTkButton(btn_row, text="Find Rooms", command=lambda: self.find_units("Room")).pack(side="left", padx=5)
        ctk.CTkButton(btn_row, text="Find Cottages", command=lambda: self.find_units("Cottage")).pack(side="left", padx=5)
        
        # Restaurant Menu
        ctk.CTkButton(btn_row, text="Restaurant Menu", command=self.open_restaurant_menu, fg_color="#e67e22", hover_color="#d35400").pack(side="left", padx=5)

        # 5. Amenities & Packages
        ctk.CTkLabel(left, text="Packages & Amenities:", font=("Arial", 14, "bold")).pack(pady=(15, 5))
        svc_frame = ctk.CTkScrollableFrame(left, height=200)
        svc_frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(svc_frame, text="--- PACKAGES (Auto-Selects Room) ---", font=("Arial", 12, "bold")).pack(anchor="w")
        packs = query("SELECT * FROM service WHERE category='Package'", fetchall=True)
        self.populate_services(svc_frame, packs)
        
        ctk.CTkLabel(svc_frame, text="--- AMENITIES & ACTIVITIES ---", font=("Arial", 12, "bold")).pack(anchor="w", pady=(10,0))
        items = query("SELECT * FROM service WHERE category != 'Package' AND category != 'Food' AND service_name NOT LIKE 'Room Fee%' AND service_name NOT LIKE 'Cottage%'", fetchall=True)
        self.populate_services(svc_frame, items)

        # 6. Cart
        ctk.CTkLabel(right, text="Bill Preview", font=("Arial", 18, "bold")).pack(pady=10)
        self.cart_items_container = ctk.CTkScrollableFrame(right, height=400)
        self.cart_items_container.pack(fill="both", expand=True)
        self.total_label = ctk.CTkLabel(right, text="TOTAL: ₱0.00", font=("Arial", 20, "bold"))
        self.total_label.pack(pady=10)
        ctk.CTkButton(right, text="Confirm Reservation", command=self.process_confirmation, fg_color="green", height=50).pack(fill="x", pady=10)
        ctk.CTkButton(right, text="Clear", command=self.clear_cart, fg_color="#c0392b").pack(fill="x")

        self.update_cart_preview()

    # --- RESTAURANT MENU POPUP ---
    def open_restaurant_menu(self):
        win = ctk.CTkToplevel(self.app)
        win.title("Restaurant Menu")
        win.geometry("500x500")
        win.transient(self.app)
        
        ctk.CTkLabel(win, text="Order Food / Meals", font=("Arial", 18, "bold")).pack(pady=10)
        scroll = ctk.CTkScrollableFrame(win)
        scroll.pack(fill="both", expand=True, padx=10, pady=5)
        
        foods = query("SELECT * FROM service WHERE category='Food'", fetchall=True)
        self.populate_services(scroll, foods)
        
        ctk.CTkButton(win, text="Close / Done", command=win.destroy).pack(pady=10)

    # --- HELPERS ---
    def find_units(self, u_type):
        d_in, d_out = self.get_dates()
        if not d_in: return
        if d_in.date() < date.today(): messagebox.showerror("Error", "Past dates not allowed."); return
        
        all_units = RoomModel.get_all_rooms_status(d_in.isoformat(), d_out.isoformat(), u_type)
        if not all_units: messagebox.showerror("Info", f"No {u_type}s found."); return
        
        try: total = sum(int(v.get()) for v in self.guest_vars.values())
        except: total = 1
        
        self.open_unit_selector(all_units, total, u_type)

    def open_unit_selector(self, units, guests, u_type, package_override=None):
        win = ctk.CTkToplevel(self.app)
        win.title(f"Select {u_type}")
        win.geometry("500x500")
        
        title = f"Select {u_type} for Package" if package_override else f"Available {u_type}s"
        ctk.CTkLabel(win, text=title, font=("Arial", 18, "bold")).pack(pady=10)
        scroll = ctk.CTkScrollableFrame(win)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        sel_var = tk.StringVar(value=self.room_id_var.get())
        for u in units:
            st = u['calculated_status']; cap = u['room_capacity']
            ok = (st == 'Available'); col = "green" if ok else "red"
            
            # If triggered by a package, ensure capacity is enough
            if package_override:
                req_cap = package_override['linked_room_capacity']
                if req_cap and cap < req_cap:
                    ok = False
                    col = "gray"
                    st += " (Too Small)"

            rb = ctk.CTkRadioButton(scroll, text=f"{u['room_number']} (Cap: {cap}) - {st}", variable=sel_var, value=str(u['room_id']), state="normal" if ok else "disabled", text_color=col)
            rb.pack(anchor="w", pady=5)
            
        def confirm():
            rid = sel_var.get()
            if rid == "0": return
            sel_u = next((u for u in units if str(u['room_id']) == rid), None)
            if sel_u:
                self.room_id_var.set(rid)
                self.room_selection_display_var.set(f"{sel_u['room_number']} Selected")
                self.room_capacity_label.configure(text=f"Max Capacity: {sel_u['room_capacity']}")
                
                if package_override:
                    self.add_to_cart_logic(package_override)
                else:
                    pat = "Cottage Rental%" if u_type == "Cottage" else f"Room Fee%({sel_u['room_capacity']} Pax)%"
                    svc = query("SELECT * FROM service WHERE service_name LIKE ?", (pat,), fetchone=True)
                    self.app.cart = [x for x in self.app.cart if 'Room Fee' not in x['name'] and 'Cottage' not in x['name']]
                    if svc: self.add_to_cart_logic(svc)
                
                win.destroy()
        ctk.CTkButton(win, text="Select", command=confirm).pack(pady=10)

    def populate_services(self, parent, items):
        if not items: 
            ctk.CTkLabel(parent, text="No items.").pack()
            return
        for i in items:
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.pack(fill="x", pady=5) # Increased padding
            
            # --- FIX: FULL TEXT + WRAPPING ---
            # Removed [:40] slice and added wraplength
            text_content = f"{i['service_name']}\n₱{i['base_price']:.0f} - {i['description']}"
            
            lbl = ctk.CTkLabel(f, text=text_content, anchor="w", justify="left", wraplength=280)
            lbl.pack(side="left", fill="x", expand=True)
            
            def safe_click(item=i):
                try:
                    self.handle_service_click(item)
                except KeyError as e:
                    messagebox.showerror("System Error", f"Missing Data: {e}\n\nPlease run init_db.py to update database.")
                except Exception as e:
                    messagebox.showerror("Error", f"An error occurred: {e}")

            ctk.CTkButton(f, text="Add", width=50, height=25, command=safe_click).pack(side="right", padx=5)

    def handle_service_click(self, item):
        if item['category'] == 'Package' and item['linked_room_type']:
            room_type = item['linked_room_type']
            d_in, d_out = self.get_dates()
            if not d_in: return
            if d_in.date() < date.today(): messagebox.showerror("Error", "Past dates not allowed."); return
            
            units = RoomModel.get_all_rooms_status(d_in.isoformat(), d_out.isoformat(), room_type)
            if not units:
                messagebox.showerror("Unavailable", f"No {room_type}s available for this package.")
                return

            messagebox.showinfo("Select Room", f"This package comes with a {room_type}.\nPlease select one now.")
            try: total = sum(int(v.get()) for v in self.guest_vars.values())
            except: total = 1
            self.open_unit_selector(units, total, room_type, package_override=item)
            return

        self.add_to_cart_logic(item)

    def add_to_cart_logic(self, item):
        if item['category'] == 'Package':
             self.app.cart = [x for x in self.app.cart if x['category'] != 'Package' and 'Room Fee' not in x['name'] and 'Cottage' not in x['name']]

        for c in self.app.cart:
            if c['id'] == item['service_id']:
                c['qty'] += 1
                self.update_cart_preview(); return
        
        cat = item['category'] if 'category' in item else 'Service'
        self.app.cart.append({'id': item['service_id'], 'name': item['service_name'], 'price': item['base_price'], 'qty': 1, 'category': cat})
        self.update_cart_preview()

    def update_cart_preview(self):
        for w in self.cart_items_container.winfo_children(): w.destroy()
        fees = ResortModel.get_entrance_fees()
        try:
            a, t, k, s, p = int(self.guest_vars['adult'].get()), int(self.guest_vars['teen'].get()), int(self.guest_vars['kid'].get()), int(self.guest_vars['senior'].get()), int(self.guest_vars['pwd'].get())
        except: a=t=k=s=p=0
        
        ent_tot = (a*fees['fee_adult']) + (t*fees['fee_teen']) + (k*fees['fee_kid']) + (s*fees['fee_adult']*0.8) + (p*fees['fee_adult']*0.8)
        
        ctk.CTkLabel(self.cart_items_container, text="[Entrance Fees]", font=("Arial", 12, "bold")).pack(anchor="w")
        if a>0: self.add_line(f"Adults x{a}", a*fees['fee_adult'])
        if t>0: self.add_line(f"Kids (6+) / Teens x{t}", t*fees['fee_teen'])
        if k>0: self.add_line(f"Toddlers x{k}", k*fees['fee_kid'])
        if s>0: self.add_line(f"Seniors x{s} (20%)", s*fees['fee_adult']*0.8)
        if p>0: self.add_line(f"PWD x{p} (20%)", p*fees['fee_adult']*0.8)
        
        d_in, d_out = self.get_dates()
        nights = (d_out - d_in).days if d_in and d_out else 1
        if nights < 1: nights = 1
        
        ctk.CTkLabel(self.cart_items_container, text="[Services/Rooms]", font=("Arial", 12, "bold")).pack(anchor="w", pady=(5,0))
        svc_tot = 0
        
        for x in self.app.cart:
            is_room_related = "Room Fee" in x['name'] or x.get('category') == 'Package'
            lp = x['price'] * x['qty']
            if is_room_related and nights > 1: 
                lp *= nights
                txt = f"{x['name']} x{x['qty']} ({nights}n)"
            else: 
                txt = f"{x['name']} x{x['qty']}"
            self.add_line(txt, lp); svc_tot += lp
            
        self.current_calc_total = ent_tot + svc_tot
        self.total_label.configure(text=f"TOTAL: ₱{self.current_calc_total:,.2f}")

    # --- FIX: WRAPPING IN CART ---
    def add_line(self, t, v):
        f = ctk.CTkFrame(self.cart_items_container, fg_color="transparent", height=20)
        f.pack(fill="x")
        # Added wraplength and expanded the text area
        ctk.CTkLabel(f, text=t, font=("Arial", 12), wraplength=180, justify="left").pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(f, text=f"₱{v:,.2f}", font=("Arial", 12)).pack(side="right", anchor="n")

    def get_dates(self):
        try:
            if TKCALENDAR_AVAILABLE:
                d_in = self.checkin_widget.get_date()
                if self.type_var.get().startswith("Day Tour"): d_out = d_in
                else: d_out = self.checkout_widget.get_date()
            else:
                d_in = datetime.strptime(self.checkin_widget.get(), "%Y-%m-%d").date()
                if self.type_var.get().startswith("Day Tour"): d_out = d_in
                else: d_out = datetime.strptime(self.checkout_widget.get(), "%Y-%m-%d").date()
            return datetime.combine(d_in, datetime.min.time()), datetime.combine(d_out, datetime.min.time())
        except: return None, None

    def clear_cart(self):
        self.app.cart = []; self.room_id_var.set("0"); self.room_selection_display_var.set("No Unit Selected"); self.update_cart_preview()

    def process_confirmation(self):
        d_in, d_out = self.get_dates()
        if not d_in: messagebox.showerror("Error", "Invalid Dates"); return
        if d_in.date() < date.today(): messagebox.showerror("Error", "Past dates not allowed"); return
        
        notes = f"Day Tour: {self.start_h.get()}:{self.start_m.get()} {self.start_p.get()} - {self.end_h.get()}:{self.end_m.get()} {self.end_p.get()}" if "Day Tour" in self.type_var.get() else "Overnight"
        
        try: cts = {k: int(v.get()) for k, v in self.guest_vars.items()}
        except: cts = {}
        if sum(cts.values()) == 0: messagebox.showerror("Error", "No guests"); return
        
        has_room_item = any(x.get('category') == 'Package' or 'Room Fee' in x['name'] or 'Cottage' in x['name'] for x in self.app.cart)
        if has_room_item and (self.room_id_var.get() == "0" or not self.room_id_var.get()):
             messagebox.showerror("Error", "You selected a room/package but no unit is assigned.\nPlease re-select."); return

        if not messagebox.askyesno("Confirm", f"Total: ₱{self.current_calc_total:,.2f}\nProceed?"): return
        
        try:
            conn = get_conn(); cur = conn.cursor()
            cur.execute("""INSERT INTO reservation (customer_id, check_in_date, check_out_date, num_guests, count_adults, count_teens, count_kids, count_pwd, count_seniors, status, notes, created_at, room_id) 
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending', ?, datetime('now'), ?)""", 
                        (self.app.current_customer['customer_id'], d_in.isoformat(), d_out.isoformat(), sum(cts.values()), cts['adult'], cts['teen'], cts['kid'], cts['pwd'], cts['senior'], notes, self.room_id_var.get() if self.room_id_var.get() != "0" else None))
            rid = cur.lastrowid
            for x in self.app.cart: cur.execute("INSERT INTO reservation_services (reservation_id, service_id, quantity, service_price) VALUES (?, ?, ?, ?)", (rid, x['id'], x['qty'], x['price']))
            cur.execute("INSERT INTO billing (reservation_id, final_amount, service_charges, status, created_at) VALUES (?, ?, ?, 'Unpaid', datetime('now'))", (rid, self.current_calc_total, self.current_calc_total))
            conn.commit(); conn.close()
            messagebox.showinfo("Success", "Reservation Saved"); self.app.admin_dashboard.show_admin_customer_dashboard()
        except Exception as e: messagebox.showerror("Error", f"{e}")