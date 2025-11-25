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
        
        # State variables
        self.room_id_var = None
        self.room_selection_display_var = None
        self.room_capacity = 0
        self.room_selection_label = None
        self.room_capacity_label = None
        self.cart_items_container = None
        self.total_label = None

    def show_reservations(self):
        """Displays a list of all reservations (Admin View)."""
        self.app.window_manager.clear_container()
        
        frame = ctk.CTkScrollableFrame(self.app.container)
        frame.pack(pady=12, padx=12, expand=True, fill="both")
        
        ctk.CTkLabel(frame, text="All Reservations", font=("Helvetica", 22)).pack(pady=8)
        
        rows = query("""
            SELECT r.reservation_id, c.full_name, r.check_in_date, r.check_out_date, r.status, r.num_guests, rm.room_number
            FROM reservation r
            JOIN customer c ON r.customer_id = c.customer_id
            LEFT JOIN room rm ON r.room_id = rm.room_id
            ORDER BY r.reservation_id DESC
        """, fetchall=True)
        
        if not rows:
            ctk.CTkLabel(frame, text="No reservations found.").pack(pady=20)
        else:
            for r in rows:
                r_frame = ctk.CTkFrame(frame)
                r_frame.pack(fill='x', pady=4, padx=6)
                
                room_txt = f"Unit: {r['room_number'] if r['room_number'] else 'N/A'}"
                info = (f"ID: {r['reservation_id']} | Customer: {r['full_name']} | {room_txt}\n"
                        f"Check-in: {r['check_in_date']} | Check-out: {r['check_out_date']}\n"
                        f"Guests: {r['num_guests']} | Status: {r['status']}")
                
                ctk.CTkLabel(r_frame, text=info, justify="left").pack(side="left", padx=10, pady=5)
                
        ctk.CTkButton(frame, text="Back", command=self.app.admin_dashboard.show_admin_interface).pack(pady=12)

    def show_make_reservation(self):
        # Reset cart
        self.app.cart = []
        self.app.window_manager.clear_container()
        
        frame = ctk.CTkFrame(self.app.container)
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

        # Unit Selection
        ctk.CTkFrame(left, height=2, corner_radius=0, fg_color='gray').pack(fill='x', padx=5, pady=15)
        ctk.CTkLabel(left, text="Select Accommodation:", font=("Helvetica", 14)).pack(pady=8)

        self.room_id_var = tk.StringVar(value="0") 
        self.room_capacity = 0
        self.room_selection_display_var = tk.StringVar(value="No Unit Selected")
        
        ctk.CTkLabel(left, textvariable=self.room_selection_display_var, font=("Helvetica", 12, "bold"), text_color="#F39C12").pack(pady=2)
        self.room_capacity_label = ctk.CTkLabel(left, text="Capacity: N/A")
        self.room_capacity_label.pack(pady=2)

        # --- Helper: Check Availability ---
        def check_availability_and_select(unit_type):
            try:
                if TKCALENDAR_AVAILABLE:
                    checkin = checkin_widget.get_date()
                    checkout = checkout_widget.get_date()
                else:
                    s_in = checkin_widget.get()
                    s_out = checkout_widget.get()
                    checkin = datetime.strptime(s_in.strip(), '%Y-%m-%d').date()
                    checkout = datetime.strptime(s_out.strip(), '%Y-%m-%d').date()
                
                if checkout <= checkin:
                    messagebox.showerror('Date Error','Check-out must be after check-in')
                    return
                guests = int(str(guests_var.get()).strip())
                if guests <= 0: raise ValueError
            except:
                messagebox.showerror('Input Error','Please enter valid dates and guest count.')
                return

            all_units = RoomModel.get_available_rooms(checkin.isoformat(), checkout.isoformat())
            filtered_units = [u for u in all_units if u['type'] == unit_type]

            if not filtered_units:
                messagebox.showerror("Unavailable", f"No available {unit_type}s found.")
                self.room_id_var.set("0")
                return
            
            self.open_room_selection(filtered_units, guests, unit_type)

        # --- BUTTON ROW ---
        btn_frame = ctk.CTkFrame(left, fg_color="transparent")
        btn_frame.pack(pady=6)

        ctk.CTkButton(btn_frame, text="Find Rooms", command=lambda: check_availability_and_select('Room'), width=140).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Find Cottages", command=lambda: check_availability_and_select('Cottage'), width=140).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Restaurant Menu", command=self.open_restaurant_menu, width=140, fg_color="#e67e22", hover_color="#d35400").pack(side="left", padx=5)

        # --- ADD-ONS LIST ---
        ctk.CTkLabel(left, text="Other Amenities / Extras:", font=("Helvetica", 14)).pack(pady=8)
        svc_list_frame = ctk.CTkScrollableFrame(left, height=240)
        svc_list_frame.pack(fill="both", expand=True, padx=6)

        services = query("""
            SELECT service_id, service_name, base_price FROM service 
            WHERE service_name NOT LIKE 'Room Fee%' 
            AND service_name NOT LIKE 'Cottage%' 
            AND service_name NOT LIKE 'Meal%'
        """, fetchall=True) or []

        self.populate_service_list(svc_list_frame, services)

        # Right Side - Cart
        ctk.CTkLabel(right, text="Cart Preview", font=("Helvetica", 16)).pack(pady=8)
        cart_frame = ctk.CTkFrame(right)
        cart_frame.pack(fill='both', expand=True, padx=6, pady=6)

        self.cart_items_container = ctk.CTkScrollableFrame(cart_frame, height=380)
        self.cart_items_container.pack(fill='both', expand=True, padx=4, pady=4)

        totals_frame = ctk.CTkFrame(right)
        totals_frame.pack(fill='x', pady=6)
        self.total_label = ctk.CTkLabel(totals_frame, text='Total: ₱0.00', font=(None, 14))
        self.total_label.pack(side='left', padx=8)

        btns = ctk.CTkFrame(right)
        btns.pack(pady=8)
        ctk.CTkButton(btns, text='Clear Cart', command=lambda: (self.app.cart.clear(), self.update_cart_preview()), fg_color="#d63031").pack(side='left', padx=6)
        ctk.CTkButton(btns, text='Confirm', fg_color='#2aa198', command=lambda: self.confirm_reservation(checkin_widget, checkout_widget, guests_var)).pack(side='left', padx=6)
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
            sid = svc['service_id']
            name = svc['service_name']
            price = svc['base_price']
            
            rowf = ctk.CTkFrame(parent_frame)
            rowf.pack(fill='x', pady=4, padx=6)
            
            lbl = ctk.CTkLabel(rowf, text=f"{name}\n₱{price:.2f}", justify="left")
            lbl.pack(side='left', padx=5)
            
            qty_var = tk.StringVar(value='1')
            ctk.CTkEntry(rowf, width=40, textvariable=qty_var).pack(side='right', padx=4)
            
            mode_var = tk.StringVar(value='public')
            
            def add_action(s=sid, n=name, p=price, q=qty_var, m=mode_var):
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
                self.app.cart.append({'service_id': s, 'name': n, 'unit_price': p, 'qty': qty, 'mode': m.get()})
                self.update_cart_preview()

            ctk.CTkButton(rowf, text='Add', width=50, command=add_action).pack(side='right', padx=4)

    def update_cart_preview(self): 
        if not self.cart_items_container or not self.cart_items_container.winfo_exists(): return
        for w in self.cart_items_container.winfo_children(): w.destroy()
            
        total = 0.0
        for idx, item in enumerate(self.app.cart, start=1):
            row = ctk.CTkFrame(self.cart_items_container)
            row.pack(fill='x', pady=4, padx=6)
            ctk.CTkLabel(row, text=f"{item['name']} x{item['qty']}").pack(side='left')
            subtotal = item['unit_price'] * item['qty']
            total += subtotal
            ctk.CTkLabel(row, text=f"₱{subtotal:.2f}").pack(side='right')
            
            def make_rm(i): return lambda: (self.app.cart.pop(i), self.update_cart_preview()) 
            ctk.CTkButton(row, text='X', width=30, fg_color="red", command=make_rm(idx-1)).pack(side='right', padx=6)
            
        self.total_label.configure(text=f"Total: ₱{total:.2f}")

    def add_accommodation_to_cart(self, room):
        # 1. Determine Service Name
        service_name_pattern = ""
        if room['type'] == 'Cottage':
             service_name_pattern = "Cottage Rental%"
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
            
            unit_info_map = {}
            sorted_units = sorted(units, key=lambda x: x['room_number'])

            for unit in sorted_units:
                unit_info_map[str(unit['room_id'])] = unit
                cap = unit['room_capacity']
                is_capacity_ok = cap >= num_guests
                
                icon = "🛖" if unit_type == "Cottage" else "🛏️"
                display_text = f"{icon} {unit['room_number']} — Cap: {cap} pax"
                if not is_capacity_ok: display_text += " (TOO SMALL)"
                
                radio_btn = ctk.CTkRadioButton(
                    scroll_frame, text=display_text, variable=self.room_selection_dialog_var, 
                    value=str(unit['room_id']), state='normal' if is_capacity_ok else 'disabled', font=("Arial", 14)
                )
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

        self.app.window_manager.focus_or_create_window('room_selection', create_dialog)

    def confirm_reservation(self, checkin_widget, checkout_widget, guests_var):
        # 1. Date Validation
        if TKCALENDAR_AVAILABLE:
            try:
                checkin = checkin_widget.get_date()
                checkout = checkout_widget.get_date()
            except:
                messagebox.showerror('Date error','Invalid dates')
                return
        else:
            s_in = checkin_widget.get()
            s_out = checkout_widget.get()
            try:
                checkin = datetime.strptime(s_in.strip(), '%Y-%m-%d').date()
                checkout = datetime.strptime(s_out.strip(), '%Y-%m-%d').date()
            except:
                messagebox.showerror('Date error','Format YYYY-MM-DD required')
                return
        if checkout <= checkin:
            messagebox.showerror('Date error','Check-out must be after check-in')
            return
        
        # 2. Guest Validation
        try:
            guests = int(str(guests_var.get()).strip())
            if guests <= 0: raise ValueError
        except:
            messagebox.showerror('Guests','Invalid guest count')
            return
            
        # 3. Unit Validation
        room_id = self.room_id_var.get()
        room_id = int(room_id) if room_id.isdigit() else None
        
        requires_unit = any('Room Fee' in item['name'] or 'Cottage Rental' in item['name'] for item in self.app.cart)

        if requires_unit:
            if room_id is None or room_id == 0:
                messagebox.showerror('Selection Error', 'This reservation includes accommodation. Please select a unit.')
                return
            
            room_cap = RoomModel.get_room_capacity(room_id)
            if guests > room_cap:
                 messagebox.showerror('Capacity Error', f'Selected unit (Capacity: {room_cap}) cannot accommodate {guests} guests.')
                 return
        else:
             room_id = None

        # 4. Global Capacity Check
        is_avail, max_cap, current_load = ResortModel.check_capacity_availability(checkin.isoformat(), checkout.isoformat(), guests)
        if not is_avail:
            messagebox.showerror("Capacity Reached", f"Cannot proceed. Resort full.\nLimit: {max_cap}\nCurrent Load: {current_load}")
            return

        # 5. Calculation
        total = sum(item['unit_price'] * item['qty'] for item in self.app.cart)
        items_summary = '\n'.join([f"{i['name']} ({i['mode']}) x{i['qty']} = ₱{i['unit_price']*i['qty']:.2f}" for i in self.app.cart])
        
        confirm = messagebox.askyesno('Confirm Reservation', f"Check-in: {checkin}\nCheck-out: {checkout}\nGuests: {guests}\n\n{items_summary}\n\nTotal: ₱{total:.2f}\n\nProceed?")
        if not confirm: return
        
        # 6. Save to DB (UPDATED WITH LOCK FIX)
        conn = None
        try:
            conn = get_conn()
            try:
                cur = conn.cursor()
                created_at = datetime.now().isoformat(sep=' ', timespec='seconds')
                
                cur.execute(
                    "INSERT INTO reservation (customer_id, check_in_date, check_out_date, num_guests, status, notes, created_at, room_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (self.app.current_customer['customer_id'], checkin.isoformat(), checkout.isoformat(), guests, 'Pending', '', created_at, room_id)
                )
                reservation_id = cur.lastrowid
                
                if room_id:
                    # FIX: Execute Update directly in same connection to avoid lock
                    cur.execute("UPDATE room SET status='booked' WHERE room_id=?", (room_id,))
                
                for item in self.app.cart:
                    cur.execute("INSERT INTO reservation_services (reservation_id, service_id, quantity, service_price) VALUES (?, ?, ?, ?)",
                        (reservation_id, item['service_id'], item['qty'], item['unit_price']))
                
                cur.execute("INSERT INTO billing (reservation_id, final_amount, initial_deposit, service_charges, amount_paid, status, created_at) VALUES (?, ?, 0.0, ?, 0.0, ?, ?)",
                    (reservation_id, total, total, 'Unpaid', created_at))
                billing_id = cur.lastrowid
                conn.commit()
                
                messagebox.showinfo('Saved', f"Reservation saved. ID: {reservation_id}")
                self.app.cart = []
                self.app.admin_dashboard.show_admin_customer_dashboard()
                
            except Exception as e:
                if conn: conn.rollback()
                raise e
        except Exception as e:
            messagebox.showerror('DB Error', f"Failed to save: {e}")
        finally:
            if conn: conn.close()

    def check_in_now(self):
        if not hasattr(self.app, 'current_customer') or not self.app.current_customer:
            messagebox.showerror("Error", "No customer loaded.")
            return
        
        s_in = simpledialog.askstring("Check-in time", "Enter check-in time (HH:MM, 24h). Example: 14:30", parent=self.app)
        s_out = simpledialog.askstring("Check-out time", "Enter check-out time (HH:MM, 24h). Example: 18:00", parent=self.app)
        if not s_in or not s_out: return
        
        g = simpledialog.askstring("Guests", "Number of guests (integer):", parent=self.app)
        try:
            num_guests = int(str(g).strip())
            if num_guests <= 0: raise ValueError
        except:
            messagebox.showerror("Invalid", "Enter a valid integer for guests.")
            return
            
        try:
            t_in = datetime.strptime(s_in.strip(), "%H:%M").time()
            t_out = datetime.strptime(s_out.strip(), "%H:%M").time()
            today = date.today()
            checkin_dt = datetime.combine(today, t_in)
            checkout_dt = datetime.combine(today, t_out)
            if checkout_dt <= checkin_dt: checkout_dt += timedelta(days=1)
        except:
            messagebox.showerror("Invalid time", "Time must be in HH:MM 24-hour format.")
            return

        checkin_iso = checkin_dt.isoformat(sep=' ')
        checkout_iso = checkout_dt.isoformat(sep=' ')
        is_avail, max_cap, current_load = ResortModel.check_capacity_availability(checkin_iso, checkout_iso, num_guests)
        if not is_avail:
            messagebox.showerror("Capacity Reached", f"Cannot check-in. Resort full.\nLimit: {max_cap}\nCurrent Load: {current_load}")
            return

        available_rooms = RoomModel.get_available_rooms(checkin_iso, checkout_iso)
        suitable_rooms = [r for r in available_rooms if r['room_capacity'] >= num_guests]
        if not suitable_rooms:
            messagebox.showerror("No Room", "No suitable room available now.")
            return

        room_list_str = "\n".join([f"{r['room_id']} - {r['room_number']} (Cap: {r['room_capacity']})" for r in suitable_rooms])
        room_choice = simpledialog.askstring("Room Selection", f"Enter Unit ID. Options:\n" + room_list_str, parent=self.app)
        if not room_choice: return
        try:
            room_id = int(room_choice)
            selected_room = next(r for r in suitable_rooms if r['room_id'] == room_id)
            room_number = selected_room['room_number']
        except:
            messagebox.showerror("Invalid choice", "Provide a valid Unit ID.")
            return

        services = query("SELECT service_id, service_name, base_price FROM service WHERE service_name LIKE '%Room%' OR service_name LIKE '%Cottage%'", fetchall=True) or []
        if not services:
            messagebox.showerror("No services", "No room services found in DB.")
            return
        svc_names = [f"{s['service_id']} - {s['service_name']} (₱{s['base_price']})" for s in services]
        svc_choice = simpledialog.askstring("Service", f"Pick service by ID. Options:\n" + "\n".join(svc_names), parent=self.app)
        if not svc_choice: return
        try:
            svc_id = int(svc_choice.split()[0])
            svc_row = next(s for s in services if s['service_id'] == svc_id)
            price = svc_row['base_price']
        except:
            messagebox.showerror("Invalid choice", "Provide a service id.")
            return
        
        # DB SAVE with try/finally and LOCK FIX
        conn = None
        try:
            conn = get_conn()
            try:
                cur = conn.cursor()
                created_at = datetime.now().isoformat(sep=' ', timespec='seconds')
                cur.execute(
                    "INSERT INTO reservation (customer_id, room_id, check_in_date, check_out_date, num_guests, status, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (self.app.current_customer['customer_id'], room_id, checkin_iso, checkout_iso, num_guests, 'Checked-in', 'Instant Check-in', created_at)
                )
                reservation_id = cur.lastrowid
                
                # FIX: Execute Update directly in same connection to avoid lock
                cur.execute("UPDATE room SET status='occupied' WHERE room_id=?", (room_id,))
                
                cur.execute("INSERT INTO reservation_services (reservation_id, service_id, quantity, service_price) VALUES (?, ?, ?, ?)", (reservation_id, svc_id, 1, price))
                cur.execute("INSERT INTO billing (reservation_id, final_amount, service_charges, initial_deposit, amount_paid, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (reservation_id, price, price, 0.0, 0.0, 'Unpaid', created_at))
                billing_id = cur.lastrowid
                conn.commit()
                messagebox.showinfo("Checked-in", f"Success: Room {room_number}.\nRes ID: {reservation_id}\nBill: ₱{price} (Unpaid).")
                self.app.admin_dashboard.show_admin_customer_dashboard()
            except Exception as e:
                if conn: conn.rollback()
                raise e
        except Exception as e:
            messagebox.showerror("DB Error", f"Failed: {e}")
        finally:
            if conn: conn.close()