import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime, date, timedelta
from db import get_conn, query
from models import RoomModel

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
        # Clear the main window
        self.app.window_manager.clear_container()
        
        # Create a scrollable frame for the list
        frame = ctk.CTkScrollableFrame(self.app.container)
        frame.pack(pady=12, padx=12, expand=True, fill="both")
        
        ctk.CTkLabel(frame, text="All Reservations", font=("Helvetica", 22)).pack(pady=8)
        
        # Query all reservations joined with customer names
        rows = query("""
            SELECT r.reservation_id, c.full_name, r.check_in_date, r.check_out_date, r.status, r.num_guests
            FROM reservation r
            JOIN customer c ON r.customer_id = c.customer_id
            ORDER BY r.reservation_id DESC
        """, fetchall=True)
        
        if not rows:
            ctk.CTkLabel(frame, text="No reservations found.").pack(pady=20)
        else:
            for r in rows:
                r_frame = ctk.CTkFrame(frame)
                r_frame.pack(fill='x', pady=4, padx=6)
                
                # Format the display info
                info = (f"ID: {r['reservation_id']} | Customer: {r['full_name']}\n"
                        f"Check-in: {r['check_in_date']} | Check-out: {r['check_out_date']}\n"
                        f"Guests: {r['num_guests']} | Status: {r['status']}")
                
                ctk.CTkLabel(r_frame, text=info, justify="left").pack(side="left", padx=10, pady=5)
                
        # Back button returns to the main Admin Interface
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

        # Room Selection (NEW SECTION)
        ctk.CTkFrame(left, height=2, corner_radius=0, fg_color='gray').pack(fill='x', padx=5, pady=15)
        ctk.CTkLabel(left, text="Room Selection:", font=("Helvetica", 14)).pack(pady=8)

        self.room_id_var = tk.StringVar(value="0") # Stores the selected room_id
        self.room_capacity = 0 # Stores the capacity for validation

        self.room_selection_display_var = tk.StringVar(value="Select a Room (Click Check Availability)")
        self.room_selection_label = ctk.CTkLabel(left, textvariable=self.room_selection_display_var)
        self.room_selection_label.pack(pady=2)

        self.room_capacity_label = ctk.CTkLabel(left, text="Capacity: N/A")
        self.room_capacity_label.pack(pady=2)

        def check_availability_and_select():
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

            # 2. Get Available Rooms & Open Selection Dialog
            rooms = RoomModel.get_available_rooms(checkin.isoformat(), checkout.isoformat())
            if not rooms:
                messagebox.showerror("No Rooms", "No available rooms for the selected dates.")
                self.room_id_var.set("0")
                self.room_selection_display_var.set("NO AVAILABLE ROOMS")
                self.room_capacity = 0
                self.room_capacity_label.configure(text="Capacity: N/A")
                return
            
            self.open_room_selection(rooms, guests)

        ctk.CTkButton(left, text="Check Availability & Select Room", command=check_availability_and_select).pack(pady=6)

        # Services list 
        services = query("SELECT service_id, service_name, base_price FROM service", fetchall=True) or []
        ctk.CTkLabel(left, text="Available services:", font=("Helvetica", 14)).pack(pady=8)

        svc_list_frame = ctk.CTkScrollableFrame(left, height=280)
        svc_list_frame.pack(fill="both", expand=True, padx=6)

        svc_controls = [] 

        def add_to_cart(service_id, name, price, qty_var, mode_var):
            try:
                qty = int(str(qty_var.get()).strip())
                if qty <= 0:
                    messagebox.showerror("Invalid qty", "Quantity must be at least 1")
                    return
            except Exception:
                messagebox.showerror("Invalid qty", "Quantity must be a positive integer")
                return
            
            # Access self.app.cart instead of self.cart
            for item in self.app.cart:
                if item['service_id'] == service_id and item['mode'] == mode_var.get():
                    item['qty'] += qty
                    self.update_cart_preview(right)
                    return
            
            self.app.cart.append({
                'service_id': service_id,
                'name': name,
                'unit_price': price,
                'qty': qty,
                'mode': mode_var.get()
            })
            self.update_cart_preview(right)

        for svc in services:
            sid = svc['service_id']
            name = svc['service_name']
            price = svc['base_price']
            rowf = ctk.CTkFrame(svc_list_frame)
            rowf.pack(fill='x', pady=4, padx=6)
            lbl = ctk.CTkLabel(rowf, text=f"{name} (₱{price})")
            lbl.pack(side='left')
            
            qty_var = tk.StringVar(value='1')
            qty_entry = ctk.CTkEntry(rowf, width=60, textvariable=qty_var)
            qty_entry.pack(side='right', padx=6)
            
            mode_var = tk.StringVar(value='public')
            rm = ctk.CTkOptionMenu(rowf, values=['public','private'], variable=mode_var, width=100)
            rm.pack(side='right', padx=6)
            
            add_btn = ctk.CTkButton(rowf, text='Add', width=60, command=lambda s=sid, n=name, p=price, q=qty_var, m=mode_var: add_to_cart(s,n,p,q,m))
            add_btn.pack(side='right', padx=6)
            svc_controls.append((sid, name, price, qty_var, mode_var, add_btn))

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
                self.update_cart_preview(right)

        btns = ctk.CTkFrame(right)
        btns.pack(pady=8)
        ctk.CTkButton(btns, text='Clear Cart', command=clear_cart_action).pack(side='left', padx=6)
        
        # Confirm Button
        ctk.CTkButton(
            btns, 
            text='Confirm Reservation', 
            fg_color='#2aa198', 
            command=lambda: self.confirm_reservation(checkin_widget, checkout_widget, guests_var)
        ).pack(side='left', padx=6)
        
        # Cancel Button -> Routes to Admin Customer Dashboard
        ctk.CTkButton(
            btns, 
            text='Cancel', 
            command=self.app.admin_dashboard.show_admin_customer_dashboard
        ).pack(side='left', padx=6)

        self.update_cart_preview(right)

    def update_cart_preview(self, parent_frame=None):
        if not self.cart_items_container or not self.cart_items_container.winfo_exists():
            return
            
        for w in self.cart_items_container.winfo_children():
            w.destroy()
            
        total = 0.0
        # Use self.app.cart
        for idx, item in enumerate(self.app.cart, start=1):
            row = ctk.CTkFrame(self.cart_items_container)
            row.pack(fill='x', pady=4, padx=6)
            ctk.CTkLabel(row, text=f"{item['name']} ({item['mode']}) x{item['qty']}").pack(side='left')
            subtotal = item['unit_price'] * item['qty']
            total += subtotal
            ctk.CTkLabel(row, text=f"₱{subtotal:.2f}").pack(side='right')
            
            def make_rm(i):
                return lambda: (self.app.cart.pop(i), self.update_cart_preview(parent_frame))
                
            ctk.CTkButton(row, text='Remove', width=80, command=make_rm(idx-1)).pack(side='right', padx=6)
            
        self.total_label.configure(text=f"Total: ₱{total:.2f}")

    def open_room_selection(self, rooms, num_guests):
        def create_dialog():
            # Parent is self.app
            dialog = ctk.CTkToplevel(self.app)
            dialog.title("Select an Available Room")
            dialog.geometry("500x400")
            dialog.transient(self.app)
            dialog.grab_set()

            ctk.CTkLabel(dialog, text=f"Select Room for {num_guests} Guests", font=("Helvetica", 18)).pack(pady=10)
            
            scroll_frame = ctk.CTkScrollableFrame(dialog)
            scroll_frame.pack(padx=10, pady=5, fill="both", expand=True)

            self.room_selection_dialog_var = tk.StringVar(value=self.room_id_var.get())
            selected_room_id = self.room_id_var.get() if self.room_id_var.get() != "0" else None
            
            room_info_map = {}
            for room in rooms:
                room_info_map[str(room['room_id'])] = room
                
                # Determine if room capacity is sufficient
                is_capacity_ok = room['room_capacity'] >= num_guests
                capacity_text = f"Capacity: {room['room_capacity']}"
                if not is_capacity_ok:
                    capacity_text += " (TOO SMALL)"
                
                # Radio button text
                room_display = f"Room {room['room_number']} - {capacity_text}"
                
                radio_btn = ctk.CTkRadioButton(scroll_frame, 
                    text=room_display, 
                    variable=self.room_selection_dialog_var, 
                    value=str(room['room_id']), 
                    state='normal' if is_capacity_ok else 'disabled')
                radio_btn.pack(anchor='w', padx=10, pady=4)
                
                # Select the previously selected room if capacity is still okay
                if str(room['room_id']) == selected_room_id and is_capacity_ok:
                    radio_btn.select()
                
            def on_confirm():
                selected_id = self.room_selection_dialog_var.get()
                if selected_id == "":
                    messagebox.showerror("Error", "Please select a room.")
                    return
                
                room = room_info_map.get(selected_id)
                if not room:
                    messagebox.showerror("Error", "Invalid room selection.")
                    return
                    
                # Update main window variables
                self.room_id_var.set(selected_id)
                self.room_selection_display_var.set(f"Room {room['room_number']} Selected")
                self.room_capacity = room['room_capacity']
                self.room_capacity_label.configure(text=f"Capacity: {self.room_capacity}")
                dialog.destroy()
                
            ctk.CTkButton(dialog, text="Confirm Selection", command=on_confirm).pack(pady=10)
            ctk.CTkButton(dialog, text="Cancel", command=dialog.destroy).pack(pady=5)
            
            return dialog

        # Use WindowManager
        self.app.window_manager.focus_or_create_window('room_selection', create_dialog)

    def confirm_reservation(self, checkin_widget, checkout_widget, guests_var):
        # 1. Date Validation
        if TKCALENDAR_AVAILABLE:
            try:
                checkin = checkin_widget.get_date()
                checkout = checkout_widget.get_date()
            except Exception:
                messagebox.showerror('Date error','Please select valid dates')
                return
        else:
            s_in = checkin_widget.get()
            s_out = checkout_widget.get()
            try:
                checkin = datetime.strptime(s_in.strip(), '%Y-%m-%d').date()
                checkout = datetime.strptime(s_out.strip(), '%Y-%m-%d').date()
            except Exception:
                messagebox.showerror('Date error','Please enter dates in YYYY-MM-DD')
                return
        
        if checkout < checkin:
            messagebox.showerror('Date error','Check-out must be after check-in')
            return
        
        # 2. Guest Validation
        try:
            guests = int(str(guests_var.get()).strip())
            if guests <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror('Guests','Enter a valid number of guests')
            return
        
        # 3. Calculation
        total = sum(item['unit_price'] * item['qty'] for item in self.app.cart)
        items_summary = '\n'.join([f"{i['name']} ({i['mode']}) x{i['qty']} = ₱{i['unit_price']*i['qty']:.2f}" for i in self.app.cart])
        
        confirm = messagebox.askyesno(
            'Confirm Reservation', 
            f"Check-in: {checkin}\nCheck-out: {checkout}\nGuests: {guests}\n\nServices:\n{items_summary if items_summary else 'No services selected'}\n\nTotal: ₱{total:.2f}\n\nProceed to save reservation?"
        )
        if not confirm:
            return
        
        # 4. Save to DB
        try:
            conn = get_conn()
            cur = conn.cursor()
            created_at = datetime.now().isoformat(sep=' ', timespec='seconds')
            
            # Access self.app.current_customer
            cur.execute(
                "INSERT INTO reservation (customer_id, check_in_date, check_out_date, num_guests, status, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (self.app.current_customer['customer_id'], checkin.isoformat(), checkout.isoformat(), guests, 'Pending', '', created_at)
            )
            reservation_id = cur.lastrowid
            
            for item in self.app.cart:
                cur.execute(
                    "INSERT INTO reservation_services (reservation_id, service_id, quantity, service_price) VALUES (?, ?, ?, ?)",
                    (reservation_id, item['service_id'], item['qty'], item['unit_price'])
                )
            
            cur.execute(
                "INSERT INTO billing (reservation_id, final_amount, status, created_at) VALUES (?, ?, ?, ?)",
                (reservation_id, total, 'Unpaid', created_at)
            )
            billing_id = cur.lastrowid
            conn.commit()
            conn.close()
            
            messagebox.showinfo('Saved', f"Reservation saved. ID: {reservation_id}. Billing ID: {billing_id}")
            self.app.cart = []
            
            # Navigate back
            self.app.admin_dashboard.show_admin_customer_dashboard()
            
        except Exception as e:
            messagebox.showerror('DB Error', f"Failed to save reservation: {e}")

    def check_in_now(self):
        if not hasattr(self.app, 'current_customer') or not self.app.current_customer:
            messagebox.showerror("Error", "No customer loaded.")
            return
            
        # Parent is self.app
        s_in = simpledialog.askstring("Check-in time", "Enter check-in time (HH:MM, 24h). Example: 14:30", parent=self.app)
        s_out = simpledialog.askstring("Check-out time", "Enter check-out time (HH:MM, 24h). Example: 18:00", parent=self.app)
        
        if not s_in or not s_out:
            return
        try:
            t_in = datetime.strptime(s_in.strip(), "%H:%M").time()
            t_out = datetime.strptime(s_out.strip(), "%H:%M").time()
        except Exception:
            messagebox.showerror("Invalid time", "Time must be in HH:MM 24-hour format.")
            return
            
        services = query("SELECT service_id, service_name, base_price FROM service", fetchall=True) or []
        if not services:
            messagebox.showerror("No services", "No services found in DB.")
            return
            
        svc_names = [f"{s['service_id']} - {s['service_name']} (₱{s['base_price']})" for s in services]
        svc_choice = simpledialog.askstring("Service", f"Pick service by entering its ID. Options:\n" + "\n".join(svc_names), parent=self.app)
        
        if not svc_choice:
            return
        try:
            svc_id = int(svc_choice.split()[0])
        except Exception:
            messagebox.showerror("Invalid choice", "Provide a service id number from the list.")
            return
            
        mode_choice = simpledialog.askstring("Mode", "Enter 'public' or 'private'", parent=self.app)
        if not mode_choice or mode_choice.lower() not in ("public","private"):
            messagebox.showerror("Invalid", "Mode must be 'public' or 'private'.")
            return
        mode_choice = mode_choice.lower()
        
        g = simpledialog.askstring("Guests", "Number of guests (integer):", parent=self.app)
        try:
            num_guests = int(str(g).strip())
            if num_guests <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror("Invalid", "Enter a valid integer for guests.")
            return
            
        today = date.today()
        checkin_dt = datetime.combine(today, t_in)
        checkout_dt = datetime.combine(today, t_out)
        
        if checkout_dt <= checkin_dt:
            checkout_dt += timedelta(days=1)
            
        try:
            conn = get_conn()
            cur = conn.cursor()
            created_at = datetime.now().isoformat(sep=' ', timespec='seconds')
            
            cur.execute(
                "INSERT INTO reservation (customer_id, check_in_date, check_out_date, num_guests, status, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (self.app.current_customer['customer_id'], checkin_dt.isoformat(sep=' '), checkout_dt.isoformat(sep=' '), num_guests, 'Checked-in', f"Mode:{mode_choice}", created_at)
            )
            reservation_id = cur.lastrowid
            
            svc_row = None
            for s in services:
                if s['service_id'] == svc_id:
                    svc_row = s
                    break
            price = svc_row['base_price'] if svc_row else 0.0
            
            cur.execute(
                "INSERT INTO reservation_services (reservation_id, service_id, quantity, service_price) VALUES (?, ?, ?, ?)",
                (reservation_id, svc_id, 1, price)
            )
            
            cur.execute(
                "INSERT INTO billing (reservation_id, final_amount, status, created_at) VALUES (?, ?, ?, ?)",
                (reservation_id, price, 'Paid', created_at)
            )
            billing_id = cur.lastrowid
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Checked-in", f"Checked in successfully. Reservation ID: {reservation_id}")
            
            # Navigate back
            self.app.admin_dashboard.show_admin_customer_dashboard()
            
        except Exception as e:
            messagebox.showerror("DB Error", f"Failed to save check-in: {e}")