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
        """
        Initialize the ReservationController.
        :param app: Reference to the main application class.
        """
        self.app = app
        
        # State variables for the specific reservation flow
        self.room_id_var = None
        self.room_selection_display_var = None
        self.room_capacity = 0
        self.room_selection_label = None
        self.room_capacity_label = None
        self.cart_items_container = None
        self.total_label = None

    def show_reservations(self):
        """
        Displays a list of all reservations in the system (Admin View).
        """
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
        # Reset cart in global app state
        self.app.cart = []
        
        # Use WindowManager to clear
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
        ctk.CTkLabel(left, text="Unit Selection:", font=("Helvetica", 14)).pack(pady=8)

        self.room_id_var = tk.StringVar(value="0") 
        self.room_capacity = 0

        self.room_selection_display_var = tk.StringVar(value="No Unit Selected")
        self.room_selection_label = ctk.CTkLabel(left, textvariable=self.room_selection_display_var, font=("Helvetica", 12, "bold"))
        self.room_selection_label.pack(pady=2)

        self.room_capacity_label = ctk.CTkLabel(left, text="Capacity: N/A")
        self.room_capacity_label.pack(pady=2)

        # --- Button Handling Logic (Room vs Cottage) ---
        def check_availability_and_select(unit_type):
            # 1. Date and Guest validation
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
                if guests <= 0:
                    messagebox.showerror('Guests','Enter a valid number of guests')
                    return

            except Exception:
                messagebox.showerror('Input Error','Please enter valid dates (YYYY-MM-DD) and a valid number of guests.')
                return

            # 2. Get Available Rooms from DB
            all_units = RoomModel.get_available_rooms(checkin.isoformat(), checkout.isoformat())
            
            # 3. Filter by Type ('Room' or 'Cottage')
            filtered_units = [u for u in all_units if u['type'] == unit_type]

            if not filtered_units:
                messagebox.showerror("Unavailable", f"No available {unit_type}s found for these dates.")
                self.room_id_var.set("0")
                return
            
            # 4. Open Selection Dialog
            self.open_room_selection(filtered_units, guests, unit_type)

        # --- TWO SEPARATE BUTTONS ---
        btn_frame = ctk.CTkFrame(left, fg_color="transparent")
        btn_frame.pack(pady=6)

        ctk.CTkButton(
            btn_frame, 
            text="Check Available Rooms", 
            command=lambda: check_availability_and_select('Room'),
            width=180
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame, 
            text="Check Available Cottages", 
            command=lambda: check_availability_and_select('Cottage'),
            width=180
        ).pack(side="left", padx=10)


        # Services list 
        services = query("SELECT service_id, service_name, base_price FROM service", fetchall=True) or []
        ctk.CTkLabel(left, text="Available services:", font=("Helvetica", 14)).pack(pady=8)

        svc_list_frame = ctk.CTkScrollableFrame(left, height=260)
        svc_list_frame.pack(fill="both", expand=True, padx=6)

        def add_to_cart(service_id, name, price, qty_var, mode_var):
            try:
                qty = int(str(qty_var.get()).strip())
                if qty <= 0: raise ValueError
            except:
                messagebox.showerror("Invalid qty", "Quantity must be a positive integer")
                return
            
            for item in self.app.cart:
                if item['service_id'] == service_id:
                    item['qty'] += qty
                    self.update_cart_preview()
                    return
            
            self.app.cart.append({
                'service_id': service_id,
                'name': name,
                'unit_price': price,
                'qty': qty,
                'mode': mode_var.get()
            })
            self.update_cart_preview()

        for svc in services:
            sid = svc['service_id']
            name = svc['service_name']
            price = svc['base_price']
            rowf = ctk.CTkFrame(svc_list_frame)
            rowf.pack(fill='x', pady=4, padx=6)
            lbl = ctk.CTkLabel(rowf, text=f"{name} (₱{price})")
            lbl.pack(side='left')
            
            qty_var = tk.StringVar(value='1')
            ctk.CTkEntry(rowf, width=50, textvariable=qty_var).pack(side='right', padx=4)
            
            mode_var = tk.StringVar(value='public')
            ctk.CTkOptionMenu(rowf, values=['public','private'], variable=mode_var, width=80).pack(side='right', padx=4)
            
            ctk.CTkButton(rowf, text='Add', width=50, command=lambda s=sid, n=name, p=price, q=qty_var, m=mode_var: add_to_cart(s,n,p,q,m)).pack(side='right', padx=4)

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

        def clear_cart_action(): 
            if messagebox.askyesno('Clear Cart','Remove all items from cart?'):
                self.app.cart = []
                self.update_cart_preview()

        btns = ctk.CTkFrame(right)
        btns.pack(pady=8)
        ctk.CTkButton(btns, text='Clear Cart', command=clear_cart_action, fg_color="#d63031").pack(side='left', padx=6)
        
        ctk.CTkButton(
            btns, 
            text='Confirm Reservation', 
            fg_color='#2aa198', 
            command=lambda: self.confirm_reservation(checkin_widget, checkout_widget, guests_var)
        ).pack(side='left', padx=6)
        
        ctk.CTkButton(
            btns, 
            text='Cancel', 
            command=self.app.admin_dashboard.show_admin_customer_dashboard
        ).pack(side='left', padx=6)

        self.update_cart_preview()

    def update_cart_preview(self): 
        if not self.cart_items_container or not self.cart_items_container.winfo_exists():
            return
            
        for w in self.cart_items_container.winfo_children():
            w.destroy()
            
        total = 0.0
        for idx, item in enumerate(self.app.cart, start=1):
            row = ctk.CTkFrame(self.cart_items_container)
            row.pack(fill='x', pady=4, padx=6)
            ctk.CTkLabel(row, text=f"{item['name']} ({item['mode']}) x{item['qty']}").pack(side='left')
            subtotal = item['unit_price'] * item['qty']
            total += subtotal
            ctk.CTkLabel(row, text=f"₱{subtotal:.2f}").pack(side='right')
            
            def make_rm(i):
                return lambda: (self.app.cart.pop(i), self.update_cart_preview()) 
                
            ctk.CTkButton(row, text='X', width=30, fg_color="red", command=make_rm(idx-1)).pack(side='right', padx=6)
            
        self.total_label.configure(text=f"Total: ₱{total:.2f}")

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
            # Sort by unit number
            sorted_units = sorted(units, key=lambda x: x['room_number'])

            for unit in sorted_units:
                unit_info_map[str(unit['room_id'])] = unit
                
                cap = unit['room_capacity']
                is_capacity_ok = cap >= num_guests
                
                icon = "🛖" if unit_type == "Cottage" else "🛏️"
                
                capacity_text = f"{cap} pax"
                if not is_capacity_ok:
                    capacity_text += " (TOO SMALL)"
                
                display_text = f"{icon} {unit['room_number']} — Capacity: {capacity_text}"
                
                radio_btn = ctk.CTkRadioButton(
                    scroll_frame, 
                    text=display_text, 
                    variable=self.room_selection_dialog_var, 
                    value=str(unit['room_id']), 
                    state='normal' if is_capacity_ok else 'disabled',
                    font=("Arial", 14)
                )
                radio_btn.pack(anchor='w', padx=10, pady=6)
                
                if str(unit['room_id']) == selected_room_id and is_capacity_ok:
                    radio_btn.select()
                
            def on_confirm():
                selected_id = self.room_selection_dialog_var.get()
                if selected_id == "" or selected_id == "0":
                    messagebox.showerror("Error", "Please select an option.")
                    return
                
                unit = unit_info_map.get(selected_id)
                
                # Update main window variables
                self.room_id_var.set(selected_id)
                self.room_selection_display_var.set(f"{unit['room_number']} Selected")
                self.room_capacity = unit['room_capacity']
                self.room_capacity_label.configure(text=f"Max Capacity: {self.room_capacity}")
                dialog.destroy()
                
            ctk.CTkButton(dialog, text="Confirm Selection", command=on_confirm, fg_color="#2aa198").pack(pady=10)
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
        
        requires_unit = any('Room' in item['name'] or 'Cottage' in item['name'] for item in self.app.cart)

        if requires_unit:
            if room_id is None or room_id == 0:
                messagebox.showerror('Selection Error', 'This reservation includes a room/cottage service. Please select a unit.')
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
        
        # 6. Save to DB
        try:
            conn = get_conn()
            cur = conn.cursor()
            created_at = datetime.now().isoformat(sep=' ', timespec='seconds')
            
            cur.execute(
                "INSERT INTO reservation (customer_id, check_in_date, check_out_date, num_guests, status, notes, created_at, room_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (self.app.current_customer['customer_id'], checkin.isoformat(), checkout.isoformat(), guests, 'Pending', '', created_at, room_id)
            )
            reservation_id = cur.lastrowid
            
            if room_id:
                RoomModel.set_room_status(room_id, 'booked') 
            
            for item in self.app.cart:
                cur.execute(
                    "INSERT INTO reservation_services (reservation_id, service_id, quantity, service_price) VALUES (?, ?, ?, ?)",
                    (reservation_id, item['service_id'], item['qty'], item['unit_price'])
                )
            
            cur.execute(
                "INSERT INTO billing (reservation_id, final_amount, initial_deposit, service_charges, amount_paid, status, created_at) VALUES (?, ?, 0.0, ?, 0.0, ?, ?)",
                (reservation_id, total, total, 'Unpaid', created_at) 
            )
            billing_id = cur.lastrowid
            conn.commit()
            conn.close()
            
            messagebox.showinfo('Saved', f"Reservation saved. ID: {reservation_id}")
            self.app.cart = []
            self.app.admin_dashboard.show_admin_customer_dashboard()
            
        except Exception as e:
            messagebox.showerror('DB Error', f"Failed to save: {e}")

    def check_in_now(self):
        if not hasattr(self.app, 'current_customer') or not self.app.current_customer:
            messagebox.showerror("Error", "No customer loaded.")
            return
            
        # 1. Gather time/guest info
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

        # 2. Global Capacity Check
        checkin_iso = checkin_dt.isoformat(sep=' ')
        checkout_iso = checkout_dt.isoformat(sep=' ')
        
        is_avail, max_cap, current_load = ResortModel.check_capacity_availability(checkin_iso, checkout_iso, num_guests)
        if not is_avail:
            messagebox.showerror("Capacity Reached", f"Cannot check-in. Resort full.\nLimit: {max_cap}\nCurrent Load: {current_load}")
            return

        # 3. Select Room (Must be available NOW)
        available_rooms = RoomModel.get_available_rooms(checkin_iso, checkout_iso)
        suitable_rooms = [r for r in available_rooms if r['room_capacity'] >= num_guests]
        
        if not suitable_rooms:
            messagebox.showerror("No Room", "No suitable room available now.")
            return

        # Simplified list selection for check-in now (could be improved to UI dialog, but simpledialog is robust here)
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
            
        # 4. Select Service
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
        
        # 5. Finalize
        try:
            conn = get_conn()
            cur = conn.cursor()
            created_at = datetime.now().isoformat(sep=' ', timespec='seconds')
            
            cur.execute(
                "INSERT INTO reservation (customer_id, room_id, check_in_date, check_out_date, num_guests, status, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (self.app.current_customer['customer_id'], room_id, checkin_iso, checkout_iso, num_guests, 'Checked-in', 'Instant Check-in', created_at)
            )
            reservation_id = cur.lastrowid
            
            RoomModel.set_room_status(room_id, 'occupied') 
            
            cur.execute("INSERT INTO reservation_services (reservation_id, service_id, quantity, service_price) VALUES (?, ?, ?, ?)", (reservation_id, svc_id, 1, price))
            cur.execute("INSERT INTO billing (reservation_id, final_amount, service_charges, initial_deposit, amount_paid, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (reservation_id, price, price, 0.0, 0.0, 'Unpaid', created_at))
            billing_id = cur.lastrowid
            
            conn.commit()
            conn.close()
            messagebox.showinfo("Checked-in", f"Success: Room {room_number}.\nRes ID: {reservation_id}\nBill: ₱{price} (Unpaid).")
            self.app.admin_dashboard.show_admin_customer_dashboard()
            
        except Exception as e:
            messagebox.showerror("DB Error", f"Failed: {e}")