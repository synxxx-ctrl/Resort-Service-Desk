# reservation_controller.py

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime, date, timedelta
from db import get_conn, query
from models import RoomModel

# Optional: If you have tkcalendar installed
try:
    from tkcalendar import DateEntry
    TKCALENDAR_AVAILABLE = True
except ImportError:
    TKCALENDAR_AVAILABLE = False


class ReservationController:
    def __init__(self, app):
        """
        app = reference to MainApp
        """
        self.app = app
        self.cart = []

    # ------------------------------------------------------------
    # SHOW MAKE RESERVATION UI
    # ------------------------------------------------------------
    def show_make_reservation(self):
        self.cart = []
        self.app.window.clear_container()

        frame = ctk.CTkFrame(self.app.container)
        frame.pack(pady=12, padx=12, expand=True, fill="both")

        left = ctk.CTkFrame(frame)
        left.pack(side="left", expand=True, fill="both", padx=12, pady=12)

        right = ctk.CTkFrame(frame, width=320)
        right.pack(side="right", fill="y", padx=12, pady=12)

        # Title
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

        # Room Selection
        ctk.CTkFrame(left, height=2, corner_radius=0, fg_color='gray').pack(fill='x', padx=5, pady=15)
        ctk.CTkLabel(left, text="Room Selection:", font=("Helvetica", 14)).pack(pady=8)
        self.room_id_var = tk.StringVar(value="0")
        self.room_capacity = 0
        self.room_selection_display_var = tk.StringVar(value="Select a Room (Click Check Availability)")
        self.room_selection_label = ctk.CTkLabel(left, textvariable=self.room_selection_display_var)
        self.room_selection_label.pack(pady=2)
        self.room_capacity_label = ctk.CTkLabel(left, text="Capacity: N/A")
        self.room_capacity_label.pack(pady=2)

        # Check Availability & Select Room
        def check_availability_and_select():
            try:
                if TKCALENDAR_AVAILABLE:
                    checkin = checkin_widget.get_date()
                    checkout = checkout_widget.get_date()
                else:
                    checkin = datetime.strptime(checkin_widget.get().strip(), '%Y-%m-%d').date()
                    checkout = datetime.strptime(checkout_widget.get().strip(), '%Y-%m-%d').date()
                guests = int(str(guests_var.get()).strip())

                if checkout <= checkin:
                    messagebox.showerror('Date Error','Check-out must be after check-in')
                    return
                if guests <= 0:
                    messagebox.showerror('Guests','Enter a valid number of guests')
                    return
            except Exception:
                messagebox.showerror('Input Error','Please enter valid dates (YYYY-MM-DD) and a valid number of guests.')
                return

            rooms = RoomModel.get_available_rooms(checkin.isoformat(), checkout.isoformat())
            if not rooms:
                messagebox.showerror("No Rooms", "No available rooms for the selected dates.")
                self.room_id_var.set("0")
                self.room_selection_display_var.set("NO AVAILABLE ROOMS")
                self.room_capacity = 0
                self.room_capacity_label.configure(text="Capacity: N/A")
                return
            self.app.open_room_selection(rooms, guests)

        ctk.CTkButton(left, text="Check Availability & Select Room", command=check_availability_and_select).pack(pady=6)

        # Services Section omitted here for brevity (similar to your previous code)
        # Use self.cart and add_to_cart as in your current implementation

        self.update_cart_preview(right)

    # ------------------------------------------------------------
    # UPDATE CART
    # ------------------------------------------------------------
    def update_cart_preview(self, parent_frame=None):
        try:
            container = self.app.cart_items_container
        except AttributeError:
            return

        for w in container.winfo_children():
            w.destroy()
        total = 0.0
        for idx, item in enumerate(self.cart, start=1):
            row = ctk.CTkFrame(container)
            row.pack(fill='x', pady=4, padx=6)
            ctk.CTkLabel(row, text=f"{item['name']} ({item['mode']}) x{item['qty']}").pack(side='left')
            subtotal = item['unit_price'] * item['qty']
            total += subtotal
            ctk.CTkLabel(row, text=f"₱{subtotal:.2f}").pack(side='right')

            def make_rm(i):
                return lambda: (self.cart.pop(i), self.update_cart_preview(parent_frame))
            ctk.CTkButton(row, text='Remove', width=80, command=make_rm(idx-1)).pack(side='right', padx=6)

        self.app.total_label.configure(text=f"Total: ₱{total:.2f}")

    # ------------------------------------------------------------
    # CONFIRM RESERVATION
    # ------------------------------------------------------------
    def confirm_reservation(self, checkin_widget, checkout_widget, guests_var):
        if TKCALENDAR_AVAILABLE:
            checkin = checkin_widget.get_date()
            checkout = checkout_widget.get_date()
        else:
            checkin = datetime.strptime(checkin_widget.get().strip(), '%Y-%m-%d').date()
            checkout = datetime.strptime(checkout_widget.get().strip(), '%Y-%m-%d').date()

        guests = int(str(guests_var.get()).strip())
        if checkout < checkin or guests <= 0:
            messagebox.showerror('Error','Invalid dates or number of guests')
            return

        total = sum(item['unit_price']*item['qty'] for item in self.cart)
        confirm = messagebox.askyesno('Confirm Reservation', f"Guests: {guests}\nTotal: ₱{total:.2f}\nProceed?")
        if not confirm:
            return

        try:
            conn = get_conn()
            cur = conn.cursor()
            created_at = datetime.now().isoformat(sep=' ', timespec='seconds')
            cur.execute(
                "INSERT INTO reservation (customer_id, check_in_date, check_out_date, num_guests, status, notes, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (self.app.current_customer['customer_id'], checkin.isoformat(), checkout.isoformat(),
                 guests, 'Pending', '', created_at)
            )
            reservation_id = cur.lastrowid
            for item in self.cart:
                cur.execute(
                    "INSERT INTO reservation_services (reservation_id, service_id, quantity, service_price) VALUES (?, ?, ?, ?)",
                    (reservation_id, item['service_id'], item['qty'], item['unit_price'])
                )
            cur.execute(
                "INSERT INTO billing (reservation_id, final_amount, status, created_at) VALUES (?, ?, ?, ?)",
                (reservation_id, total, 'Unpaid', created_at)
            )
            conn.commit()
            conn.close()
            messagebox.showinfo('Saved', f"Reservation saved. ID: {reservation_id}")
            self.cart = []
            self.app.customer.show_admin_customer_dashboard()
        except Exception as e:
            messagebox.showerror('DB Error', f"Failed to save reservation: {e}")

    def check_in_now(self):
        if not self.app.current_customer:
            messagebox.showerror("Error", "No customer loaded.")
            return

        # Ask for check-in/out times
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

        # Get available services
        from db import query, get_conn
        services = query("SELECT service_id, service_name, base_price FROM service", fetchall=True) or []
        if not services:
            messagebox.showerror("No services", "No services found in DB.")
            return

        # Choose service
        svc_names = [f"{s['service_id']} - {s['service_name']} (₱{s['base_price']})" for s in services]
        svc_choice = simpledialog.askstring(
            "Service",
            f"Pick service by entering its ID. Options:\n" + "\n".join(svc_names),
            parent=self.app
        )
        if not svc_choice:
            return

        try:
            svc_id = int(svc_choice.split()[0])
        except Exception:
            messagebox.showerror("Invalid choice", "Provide a service id number from the list.")
            return

        # Choose mode
        mode_choice = simpledialog.askstring("Mode", "Enter 'public' or 'private'", parent=self.app)
        if not mode_choice or mode_choice.lower() not in ("public", "private"):
            messagebox.showerror("Invalid", "Mode must be 'public' or 'private'.")
            return
        mode_choice = mode_choice.lower()

        # Number of guests
        g = simpledialog.askstring("Guests", "Number of guests (integer):", parent=self.app)
        try:
            num_guests = int(str(g).strip())
            if num_guests <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror("Invalid", "Enter a valid integer for guests.")
            return

        # Combine today's date with times
        today = date.today()
        checkin_dt = datetime.combine(today, t_in)
        checkout_dt = datetime.combine(today, t_out)
        if checkout_dt <= checkin_dt:
            checkout_dt += timedelta(days=1)

        # Insert reservation and billing into DB
        try:
            conn = get_conn()
            cur = conn.cursor()
            created_at = datetime.now().isoformat(sep=' ', timespec='seconds')

            # Reservation table
            cur.execute(
                "INSERT INTO reservation (customer_id, check_in_date, check_out_date, num_guests, status, notes, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    self.app.current_customer['customer_id'],
                    checkin_dt.isoformat(sep=' '),
                    checkout_dt.isoformat(sep=' '),
                    num_guests,
                    'Checked-in',
                    f"Mode:{mode_choice}",
                    created_at
                )
            )
            reservation_id = cur.lastrowid

            # Find selected service
            svc_row = next((s for s in services if s['service_id'] == svc_id), None)
            price = svc_row['base_price'] if svc_row else 0.0

            # Reservation services table
            cur.execute(
                "INSERT INTO reservation_services (reservation_id, service_id, quantity, service_price) VALUES (?, ?, ?, ?)",
                (reservation_id, svc_id, 1, price)
            )

            # Billing table
            cur.execute(
                "INSERT INTO billing (reservation_id, final_amount, status, created_at) VALUES (?, ?, ?, ?)",
                (reservation_id, price, 'Paid', created_at)
            )
            billing_id = cur.lastrowid

            conn.commit()
            conn.close()

            messagebox.showinfo("Checked-in", f"Checked in successfully.\nReservation ID: {reservation_id}")
            self.app.show_admin_customer_dashboard()
        except Exception as e:
            messagebox.showerror("DB Error", f"Failed to save check-in: {e}")
