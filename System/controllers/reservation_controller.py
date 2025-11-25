import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime, date, timedelta
from db import get_conn, query
from models import RoomModel, ResortModel

# Try importing tkcalendar
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
        self.room_selection_label = None
        self.room_capacity_label = None
        self.cart_items_container = None
        self.total_label = None
        self.checkin_widget = None
        self.checkout_widget = None
        self.type_var = None

    def show_reservations(self):
        self.app.window_manager.clear_container()
        frame = ctk.CTkScrollableFrame(self.app.container)
        frame.pack(pady=12, padx=12, expand=True, fill="both")
        ctk.CTkLabel(frame, text="All Reservations", font=("Helvetica", 22)).pack(pady=8)
        rows = query("""SELECT r.reservation_id, c.full_name, r.check_in_date, r.check_out_date, r.status, r.num_guests, rm.room_number 
                        FROM reservation r JOIN customer c ON r.customer_id = c.customer_id LEFT JOIN room rm ON r.room_id = rm.room_id ORDER BY r.reservation_id DESC""", fetchall=True)
        if not rows: ctk.CTkLabel(frame, text="No reservations found.").pack(pady=20)
        else:
            for r in rows:
                r_frame = ctk.CTkFrame(frame)
                r_frame.pack(fill='x', pady=4, padx=6)
                info = (f"ID: {r['reservation_id']} | Customer: {r['full_name']} | Unit: {r['room_number'] or 'N/A'}\n"
                        f"Dates: {r['check_in_date']} to {r['check_out_date']} | Guests: {r['num_guests']} | Status: {r['status']}")
                ctk.CTkLabel(r_frame, text=info, justify="left").pack(side="left", padx=10, pady=5)
        ctk.CTkButton(frame, text="Back", command=self.app.admin_dashboard.show_admin_interface).pack(pady=12)

    def get_stay_duration(self):
        """Calculates number of nights/days based on current widget values."""
        try:
            if self.type_var.get() == "Day Tour (Same Day)": return 1
            
            if TKCALENDAR_AVAILABLE:
                d_in = self.checkin_widget.get_date()
                d_out = self.checkout_widget.get_date()
            else:
                d_in = datetime.strptime(self.checkin_widget.get().strip(), '%Y-%m-%d').date()
                d_out = datetime.strptime(self.checkout_widget.get().strip(), '%Y-%m-%d').date()
            
            delta = (d_out - d_in).days
            return delta if delta > 0 else 1
        except:
            return 1

    def show_make_reservation(self):
        self.app.cart = []
        self.app.window_manager.clear_container()
        
        frame = ctk.CTkFrame(self.app.container)
        frame.pack(pady=12, padx=12, expand=True, fill="both")
        left = ctk.CTkFrame(frame)
        left.pack(side="left", expand=True, fill="both", padx=12, pady=12)
        right = ctk.CTkFrame(frame, width=320)
        right.pack(side="right", fill="y", padx=12, pady=12)

        ctk.CTkLabel(left, text="Create Reservation / Check-In", font=("Helvetica", 18)).pack(pady=8)

        self.type_var = tk.StringVar(value="Overnight Stay")
        def toggle_inputs(value):
            for widget in schedule_container.winfo_children(): widget.pack_forget()
            if value == "Overnight Stay": date_frame.pack(in_=schedule_container, pady=6)
            else: time_frame.pack(in_=schedule_container, pady=6)
            self.update_cart_preview()

        seg_btn = ctk.CTkSegmentedButton(left, values=["Overnight Stay", "Day Tour (Same Day)"], variable=self.type_var, command=toggle_inputs)
        seg_btn.pack(pady=10)
        seg_btn.set("Overnight Stay")

        schedule_container = ctk.CTkFrame(left, fg_color="transparent")
        schedule_container.pack(pady=5, fill="x")

        # Date Inputs
        date_frame = ctk.CTkFrame(schedule_container, fg_color="transparent")
        if TKCALENDAR_AVAILABLE:
            ctk.CTkLabel(date_frame, text="Check-in:").grid(row=0, column=0, padx=6)
            self.checkin_widget = DateEntry(date_frame, width=14)
            self.checkin_widget.grid(row=0, column=1, padx=6)
            self.checkin_widget.bind("<<DateEntrySelected>>", lambda e: self.update_cart_preview())
            
            ctk.CTkLabel(date_frame, text="Check-out:").grid(row=0, column=2, padx=6)
            self.checkout_widget = DateEntry(date_frame, width=14)
            self.checkout_widget.grid(row=0, column=3, padx=6)
            self.checkout_widget.bind("<<DateEntrySelected>>", lambda e: self.update_cart_preview())
        else:
            ctk.CTkLabel(date_frame, text="Check-in (YYYY-MM-DD):").grid(row=0, column=0, padx=6)
            self.checkin_widget = ctk.CTkEntry(date_frame, width=14)
            self.checkin_widget.grid(row=0, column=1, padx=6)
            ctk.CTkLabel(date_frame, text="Check-out (YYYY-MM-DD):").grid(row=0, column=2, padx=6)
            self.checkout_widget = ctk.CTkEntry(date_frame, width=14)
            self.checkout_widget.grid(row=0, column=3, padx=6)
            self.checkin_widget.bind("<FocusOut>", lambda e: self.update_cart_preview())
            self.checkout_widget.bind("<FocusOut>", lambda e: self.update_cart_preview())

        # Time Inputs
        time_frame = ctk.CTkFrame(schedule_container, fg_color="transparent")
        ctk.CTkLabel(time_frame, text="Today's Schedule (12-Hour Format)", font=("Arial", 12, "bold")).pack(pady=5)
        t_inner = ctk.CTkFrame(time_frame, fg_color="transparent")
        t_inner.pack()
        hours = [str(i) for i in range(1, 13)]
        global start_h, start_m, start_p, end_h, end_m, end_p
        ctk.CTkLabel(t_inner, text="Start:").grid(row=0, column=0, padx=5)
        start_h = ctk.CTkOptionMenu(t_inner, values=hours, width=60)
        start_h.grid(row=0, column=1)
        start_m = ctk.CTkOptionMenu(t_inner, values=["00","15","30","45"], width=60)
        start_m.grid(row=0, column=2)
        start_p = ctk.CTkOptionMenu(t_inner, values=["AM","PM"], width=60)
        start_p.grid(row=0, column=3, padx=5)
        start_p.set("AM")
        ctk.CTkLabel(t_inner, text="End:").grid(row=0, column=4, padx=5)
        end_h = ctk.CTkOptionMenu(t_inner, values=hours, width=60)
        end_h.grid(row=0, column=5)
        end_m = ctk.CTkOptionMenu(t_inner, values=["00","15","30","45"], width=60)
        end_m.grid(row=0, column=6)
        end_p = ctk.CTkOptionMenu(t_inner, values=["AM","PM"], width=60)
        end_p.grid(row=0, column=7, padx=5)
        end_p.set("PM")
        
        date_frame.pack(in_=schedule_container, pady=6)

        # Guest Breakdown
        guest_frame = ctk.CTkFrame(left)
        guest_frame.pack(pady=10, padx=10, fill='x')
        ctk.CTkLabel(guest_frame, text="Guest Details", font=("Helvetica", 12, "bold")).pack(pady=5)
        gf_inner = ctk.CTkFrame(guest_frame, fg_color="transparent")
        gf_inner.pack()
        ctk.CTkLabel(gf_inner, text="Adults:").grid(row=0, column=0, padx=5)
        adults_var = tk.StringVar(value="1")
        ctk.CTkEntry(gf_inner, width=50, textvariable=adults_var).grid(row=0, column=1, padx=5)
        ctk.CTkLabel(gf_inner, text="Kids:").grid(row=0, column=2, padx=5)
        kids_var = tk.StringVar(value="0")
        ctk.CTkEntry(gf_inner, width=50, textvariable=kids_var).grid(row=0, column=3, padx=5)
        ctk.CTkLabel(gf_inner, text="PWD:").grid(row=0, column=4, padx=5)
        pwd_var = tk.StringVar(value="0")
        ctk.CTkEntry(gf_inner, width=50, textvariable=pwd_var).grid(row=0, column=5, padx=5)
        ctk.CTkLabel(gf_inner, text="Seniors:").grid(row=0, column=6, padx=5)
        senior_var = tk.StringVar(value="0")
        ctk.CTkEntry(gf_inner, width=50, textvariable=senior_var).grid(row=0, column=7, padx=5)

        # Selection Display
        ctk.CTkFrame(left, height=2, corner_radius=0, fg_color='gray').pack(fill='x', padx=5, pady=15)
        ctk.CTkLabel(left, text="Select Accommodation:", font=("Helvetica", 14)).pack(pady=8)
        self.room_id_var = tk.StringVar(value="0") 
        self.room_capacity = 0
        self.room_selection_display_var = tk.StringVar(value="No Unit Selected")
        ctk.CTkLabel(left, textvariable=self.room_selection_display_var, font=("Helvetica", 12, "bold"), text_color="#F39C12").pack(pady=2)
        self.room_capacity_label = ctk.CTkLabel(left, text="Capacity: N/A")
        self.room_capacity_label.pack(pady=2)

        def get_total_guests():
            try: return int(adults_var.get() or 0) + int(kids_var.get() or 0) + int(pwd_var.get() or 0) + int(senior_var.get() or 0)
            except: return 0

        def check_availability_and_select(unit_type):
            try:
                if self.type_var.get() == "Overnight Stay":
                    if TKCALENDAR_AVAILABLE:
                        d_in, d_out = self.checkin_widget.get_date(), self.checkout_widget.get_date()
                    else:
                        d_in = datetime.strptime(self.checkin_widget.get(), '%Y-%m-%d').date()
                        d_out = datetime.strptime(self.checkout_widget.get(), '%Y-%m-%d').date()
                    checkin = datetime.combine(d_in, datetime.min.time())
                    checkout = datetime.combine(d_out, datetime.min.time())
                    if d_out <= d_in: 
                        messagebox.showerror('Date Error','Check-out must be after check-in')
                        return
                else:
                    checkin = datetime.now()
                    checkout = datetime.now() 

                guests = get_total_guests()
                if guests <= 0: 
                    messagebox.showerror('Guests','Total guests must be at least 1')
                    return
            except:
                messagebox.showerror('Input Error','Please check dates and guest numbers.')
                return

            all_units = RoomModel.get_available_rooms(checkin.isoformat(), checkout.isoformat())
            filtered_units = [u for u in all_units if u['type'] == unit_type]
            if not filtered_units:
                messagebox.showerror("Unavailable", f"No available {unit_type}s found.")
                self.room_id_var.set("0")
                return
            self.open_room_selection(filtered_units, guests, unit_type)

        btn_frame = ctk.CTkFrame(left, fg_color="transparent")
        btn_frame.pack(pady=6)
        ctk.CTkButton(btn_frame, text="Find Rooms", command=lambda: check_availability_and_select('Room'), width=140).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Find Cottages", command=lambda: check_availability_and_select('Cottage'), width=140).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Restaurant Menu", command=self.open_restaurant_menu, width=140, fg_color="#e67e22", hover_color="#d35400").pack(side="left", padx=5)

        ctk.CTkLabel(left, text="Other Amenities / Extras:", font=("Helvetica", 14)).pack(pady=8)
        svc_list_frame = ctk.CTkScrollableFrame(left, height=240)
        svc_list_frame.pack(fill="both", expand=True, padx=6)
        
        # Fetch all amenities (excluding Rooms/Cottages/Meals)
        services = query("""SELECT service_id, service_name, base_price FROM service 
                            WHERE service_name NOT LIKE 'Room Fee%' AND service_name NOT LIKE 'Cottage%' AND service_name NOT LIKE 'Meal%'""", fetchall=True) or []
        self.populate_service_list(svc_list_frame, services)

        # Cart
        ctk.CTkLabel(right, text="Cart Preview", font=("Helvetica", 16)).pack(pady=8)
        cart_frame = ctk.CTkFrame(right)
        cart_frame.pack(fill='both', expand=True, padx=6, pady=6)
        self.cart_items_container = ctk.CTkScrollableFrame(cart_frame, height=380)
        self.cart_items_container.pack(fill='both', expand=True, padx=4, pady=4)
        totals_frame = ctk.CTkFrame(right)
        totals_frame.pack(fill='x', pady=6)
        self.total_label = ctk.CTkLabel(totals_frame, text='Total: ₱0.00', font=(None, 14))
        self.total_label.pack(side='left', padx=8)

        def handle_confirm():
            mode = self.type_var.get()
            try:
                guests = get_total_guests()
                if guests <= 0: raise ValueError
                
                if mode == "Overnight Stay":
                    if TKCALENDAR_AVAILABLE:
                        d_in = self.checkin_widget.get_date()
                        d_out = self.checkout_widget.get_date()
                    else:
                        d_in = datetime.strptime(self.checkin_widget.get(), '%Y-%m-%d').date()
                        d_out = datetime.strptime(self.checkout_widget.get(), '%Y-%m-%d').date()
                    checkin_dt = datetime.combine(d_in, datetime.min.time())
                    checkout_dt = datetime.combine(d_out, datetime.min.time())
                else:
                    today = date.today()
                    s_h = int(start_h.get())
                    if start_p.get() == "PM" and s_h != 12: s_h += 12
                    if start_p.get() == "AM" and s_h == 12: s_h = 0
                    e_h = int(end_h.get())
                    if end_p.get() == "PM" and e_h != 12: e_h += 12
                    if end_p.get() == "AM" and e_h == 12: e_h = 0
                    checkin_dt = datetime.combine(today, datetime.min.time().replace(hour=s_h, minute=int(start_m.get())))
                    checkout_dt = datetime.combine(today, datetime.min.time().replace(hour=e_h, minute=int(end_m.get())))
                    if checkout_dt <= checkin_dt: checkout_dt += timedelta(days=1)

                self.confirm_reservation(checkin_dt, checkout_dt, adults_var, kids_var, pwd_var, senior_var)
            except Exception as e:
                print(e)
                messagebox.showerror("Error", "Invalid inputs.")

        btns = ctk.CTkFrame(right)
        btns.pack(pady=8)
        ctk.CTkButton(btns, text='Clear Cart', command=lambda: (self.app.cart.clear(), self.update_cart_preview()), fg_color="#d63031").pack(side='left', padx=6)
        ctk.CTkButton(btns, text='Confirm', fg_color='#2aa198', command=handle_confirm).pack(side='left', padx=6)
        ctk.CTkButton(btns, text='Cancel', command=self.app.admin_dashboard.show_admin_customer_dashboard).pack(side='left', padx=6)
        self.update_cart_preview()

    def open_restaurant_menu(self):
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Restaurant Menu")
        dialog.geometry("500x500")
        dialog.transient(self.app)
        dialog.grab_set()
        ctk.CTkLabel(dialog, text="Select Meals", font=("Helvetica", 20, "bold")).pack(pady=10)
        food_frame = ctk.CTkScrollableFrame(dialog)
        food_frame.pack(fill="both", expand=True, padx=10, pady=5)
        meals = query("SELECT service_id, service_name, base_price, description FROM service WHERE service_name LIKE 'Meal%'", fetchall=True)
        self.populate_service_list(food_frame, meals)
        ctk.CTkButton(dialog, text="Done / Close", command=dialog.destroy).pack(pady=10)

    def populate_service_list(self, parent_frame, services_data):
        for svc in services_data:
            sid, name, price = svc['service_id'], svc['service_name'], svc['base_price']
            rowf = ctk.CTkFrame(parent_frame)
            rowf.pack(fill='x', pady=4, padx=6)
            lbl = ctk.CTkLabel(rowf, text=f"{name}\n₱{price:.2f}", justify="left")
            lbl.pack(side='left', padx=5)
            qty_var = tk.StringVar(value='1')
            ctk.CTkEntry(rowf, width=40, textvariable=qty_var).pack(side='right', padx=4)
            
            def add_action(s=sid, n=name, p=price, q=qty_var):
                if "Extra Bed" in n:
                    current_room = self.room_id_var.get()
                    if not current_room or current_room == "0":
                        messagebox.showerror("Action Blocked", "You must select a Room or Cottage first before adding an Extra Bed.")
                        return
                try:
                    qty = int(str(q.get()).strip())
                    if qty <= 0: raise ValueError
                except:
                    messagebox.showerror("Invalid qty", "Quantity must be positive.")
                    return
                for item in self.app.cart:
                    if item['service_id'] == s:
                        item['qty'] += qty
                        self.update_cart_preview()
                        return
                self.app.cart.append({'service_id': s, 'name': n, 'unit_price': p, 'qty': qty, 'mode': 'public'})
                self.update_cart_preview()
            ctk.CTkButton(rowf, text='Add', width=50, command=add_action).pack(side='right', padx=4)

    def update_cart_preview(self): 
        if not self.cart_items_container or not self.cart_items_container.winfo_exists(): return
        for w in self.cart_items_container.winfo_children(): w.destroy()
        
        nights = self.get_stay_duration()
        total = 0.0
        for idx, item in enumerate(self.app.cart, start=1):
            row = ctk.CTkFrame(self.cart_items_container)
            row.pack(fill='x', pady=4, padx=6)
            
            # --- DYNAMIC PRICING APPLIED TO ALL ITEMS ---
            line_price = item['unit_price'] * item['qty'] * nights
            desc = f"{item['name']} x{item['qty']} ({nights} nights)" if nights > 1 else f"{item['name']} x{item['qty']}"

            ctk.CTkLabel(row, text=desc).pack(side='left')
            subtotal = line_price
            total += subtotal
            ctk.CTkLabel(row, text=f"₱{subtotal:.2f}").pack(side='right')
            
            def make_rm(i): return lambda: (self.app.cart.pop(i), self.update_cart_preview()) 
            ctk.CTkButton(row, text='X', width=30, fg_color="red", command=make_rm(idx-1)).pack(side='right', padx=6)
        
        self.total_label.configure(text=f"Total: ₱{total:.2f}")

    def add_accommodation_to_cart(self, room):
        service_name_pattern = ""
        if room['type'] == 'Cottage': service_name_pattern = "Cottage Rental%"
        else:
            if room['room_capacity'] == 1: service_name_pattern = "Room Fee - Single%"
            elif room['room_capacity'] == 2: service_name_pattern = "Room Fee - Double%"
            elif room['room_capacity'] == 4: service_name_pattern = "Room Fee - Family%"
            elif room['room_capacity'] == 6: service_name_pattern = "Room Fee - Suite%"
        if not service_name_pattern: return 
        svc = query("SELECT * FROM service WHERE service_name LIKE ?", (service_name_pattern,), fetchone=True)
        if svc:
            self.app.cart = [item for item in self.app.cart if "Room Fee" not in item['name'] and "Cottage Rental" not in item['name']]
            self.app.cart.append({'service_id': svc['service_id'], 'name': svc['service_name'], 'unit_price': svc['base_price'], 'qty': 1, 'mode': 'public'})
            self.update_cart_preview()

    def open_room_selection(self, units, num_guests, unit_type):
        def create_dialog():
            dialog = ctk.CTkToplevel(self.app)
            dialog.title(f"Select Available {unit_type}")
            dialog.geometry("550x500")
            dialog.transient(self.app)
            dialog.grab_set()
            ctk.CTkLabel(dialog, text=f"Select {unit_type} for {num_guests} Guests", font=("Helvetica", 18, "bold")).pack(pady=10)
            scroll_frame = ctk.CTkScrollableFrame(dialog)
            scroll_frame.pack(padx=10, pady=10, fill="both", expand=True)
            self.room_selection_dialog_var = tk.StringVar(value=self.room_id_var.get())
            selected_room_id = self.room_id_var.get() if self.room_id_var.get() != "0" else None
            sorted_units = sorted(units, key=lambda x: x['room_number'])
            for unit in sorted_units:
                unit_info_map[str(unit['room_id'])] = unit
                cap = unit['room_capacity']
                is_capacity_ok = cap >= num_guests
                icon = "🛖" if unit_type == "Cottage" else "🛏️"
                display_text = f"{icon} {unit['room_number']} — Cap: {cap} pax"
                if not is_capacity_ok: display_text += " (TOO SMALL)"
                radio_btn = ctk.CTkRadioButton(scroll_frame, text=display_text, variable=self.room_selection_dialog_var, value=str(unit['room_id']), state='normal' if is_capacity_ok else 'disabled', font=("Arial", 14))
                radio_btn.pack(anchor='w', padx=10, pady=6)
                if str(unit['room_id']) == selected_room_id and is_capacity_ok: radio_btn.select()
            def on_confirm():
                selected_id = self.room_selection_dialog_var.get()
                if selected_id == "" or selected_id == "0":
                    messagebox.showerror("Error", "Please select an option.")
                    return
                unit = unit_info_map.get(selected_id)
                self.room_id_var.set(selected_id)
                self.room_selection_display_var.set(f"{unit['room_number']} Selected")
                self.room_capacity = unit['room_capacity']
                self.room_capacity_label.configure(text=f"Max Capacity: {self.room_capacity}")
                self.add_accommodation_to_cart(unit)
                dialog.destroy()
            ctk.CTkButton(dialog, text="Confirm", command=on_confirm, fg_color="#2aa198").pack(pady=10)
            ctk.CTkButton(dialog, text="Cancel", command=dialog.destroy, fg_color="transparent", border_width=1).pack(pady=5)
            return dialog
        unit_info_map = {}
        self.app.window_manager.focus_or_create_window('room_selection', create_dialog)

    def confirm_reservation(self, checkin_dt, checkout_dt, a_var, k_var, p_var, s_var):
        a, k, p, s = int(a_var.get() or 0), int(k_var.get() or 0), int(p_var.get() or 0), int(s_var.get() or 0)
        guests = a + k + p + s
        
        room_id = self.room_id_var.get()
        room_id = int(room_id) if room_id.isdigit() else None
        requires_unit = any('Room Fee' in item['name'] or 'Cottage Rental' in item['name'] for item in self.app.cart)
        if requires_unit:
            if room_id is None or room_id == 0:
                messagebox.showerror('Selection Error', 'Select a unit first.')
                return
            if guests > RoomModel.get_room_capacity(room_id):
                 messagebox.showerror('Capacity Error', 'Unit too small.')
                 return
        else: room_id = None

        is_avail, max_cap, current_load = ResortModel.check_capacity_availability(checkin_dt.isoformat(), checkout_dt.isoformat(), guests)
        if not is_avail:
            messagebox.showerror("Capacity Reached", "Resort full.")
            return

        # Recalculate Total for Saving (Multiply everything by nights)
        nights = self.get_stay_duration()
        subtotal = 0
        for item in self.app.cart:
            line = item['unit_price'] * item['qty'] * nights
            subtotal += line
        
        discount_amount = 0.0
        if guests > 0:
            per_person_avg = subtotal / guests
            discount_amount += (p * per_person_avg * 0.20)
            discount_amount += (s * per_person_avg * 0.20)
        
        final_total = subtotal - discount_amount
        
        msg = (f"Check-in: {checkin_dt}\nDuration: {nights} Nights\nGuests: {guests} (A:{a}, K:{k}, P:{p}, S:{s})\n"
               f"Subtotal: ₱{subtotal:.2f}\nDiscount (PWD/Senior): -₱{discount_amount:.2f}\nTOTAL: ₱{final_total:.2f}\n\nProceed?")
        
        if not messagebox.askyesno('Confirm', msg): return
        
        conn = None
        try:
            conn = get_conn()
            try:
                cur = conn.cursor()
                created_at = datetime.now().isoformat(sep=' ', timespec='seconds')
                status = 'Checked-in' if checkin_dt.date() == date.today() else 'Pending'
                
                cur.execute("INSERT INTO reservation (customer_id, check_in_date, check_out_date, num_guests, count_adults, count_kids, count_pwd, count_seniors, status, notes, created_at, room_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (self.app.current_customer['customer_id'], checkin_dt.isoformat(), checkout_dt.isoformat(), guests, a, k, p, s, status, '', created_at, room_id))
                reservation_id = cur.lastrowid
                
                if room_id:
                    r_status = 'occupied' if status == 'Checked-in' else 'booked'
                    cur.execute("UPDATE room SET status=? WHERE room_id=?", (r_status, room_id))
                
                for item in self.app.cart:
                    # Store quantity as the raw selection, but price is implicit in bill
                    cur.execute("INSERT INTO reservation_services (reservation_id, service_id, quantity, service_price) VALUES (?, ?, ?, ?)",
                        (reservation_id, item['service_id'], item['qty'], item['unit_price']))
                
                cur.execute("INSERT INTO billing (reservation_id, final_amount, discount_amount, initial_deposit, service_charges, amount_paid, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (reservation_id, final_total, discount_amount, 0.0, subtotal, 0.0, 'Unpaid', created_at))
                conn.commit()
                messagebox.showinfo('Saved', f"Reservation saved. ID: {reservation_id}")
                self.app.cart = []
                self.app.admin_dashboard.show_admin_customer_dashboard()
            except Exception as e:
                if conn: conn.rollback()
                raise e
        except Exception as e:
            messagebox.showerror('DB Error', f"Failed: {e}")
        finally:
            if conn: conn.close()

    def check_in_now(self): pass