from db import query, execute
from datetime import datetime

class AdminModel:
    
    @staticmethod
    def check_login(username, password):
        row = query("SELECT * FROM admin WHERE username = ?", (username,), fetchone=True)
        if not row:
            return False
        return row['password'] == password

    @staticmethod
    def change_credentials(admin_id, new_username, new_password):
        execute("UPDATE admin SET username=?, password=? WHERE admin_id=?", (new_username, new_password, admin_id))

    @staticmethod
    def get_reservations():
        return query("SELECT r.*, c.full_name, c.username as customer_code FROM reservation r JOIN customer c ON r.customer_id = c.customer_id ORDER BY r.created_at DESC")

    @staticmethod
    def get_transaction_logs():
        return query("SELECT p.*, c.full_name, c.username as customer_code FROM payment p LEFT JOIN customer c ON p.customer_id = c.customer_id ORDER BY p.payment_date DESC")

    @staticmethod
    def get_checked_in_reservations():
        """Fetches all reservations currently marked as Checked-in."""
        return query("""
            SELECT 
                r.*, c.full_name, c.username as customer_code, rm.room_number
            FROM reservation r 
            JOIN customer c ON r.customer_id = c.customer_id
            LEFT JOIN room rm ON r.room_id = rm.room_id
            WHERE r.status = 'Checked-in'
            ORDER BY r.check_in_date ASC
        """, fetchall=True)

    @staticmethod
    def generate_report():
        services_used = query("SELECT s.service_id, s.service_name, COUNT(rs.service_id) as usage_count, SUM(rs.service_price * rs.quantity) as income FROM reservation_services rs JOIN service s ON rs.service_id = s.service_id GROUP BY rs.service_id")
        total_income_row = query("SELECT SUM(final_amount) as total FROM billing", fetchone=True)
        total_income = total_income_row['total'] if total_income_row and total_income_row['total'] is not None else 0
        return {'services': services_used, 'total_income': total_income}

class CustomerModel:

    @staticmethod
    def create_customer(username, full_name, email, contact_number):
        return execute("INSERT INTO customer (username, full_name, email, contact_number) VALUES (?, ?, ?, ?)", (username, full_name, email, contact_number))

    @staticmethod
    def get_customer_by_code(code):
        return query("SELECT * FROM customer WHERE username = ?", (code,), fetchone=True)

    @staticmethod
    def add_reservation(customer_id, check_in, check_out, num_guests, room_id=None, notes=''):
        rid = execute("INSERT INTO reservation (customer_id, room_id, check_in_date, check_out_date, num_guests, status, notes, created_at) VALUES (?, ?, ?, ?, ?, 'pending', ?, datetime('now'))", (customer_id, room_id, check_in, check_out, num_guests, notes))

    @staticmethod
    def add_reservation_service(reservation_id, service_id, qty, price):
        execute("INSERT INTO reservation_services (reservation_id, service_id, quantity, service_price) VALUES (?, ?, ?, ?)", (reservation_id, service_id, qty, price))

    @staticmethod
    def get_customer_by_id(customer_id):
        return query("SELECT * FROM customer WHERE customer_id=?", (customer_id,), fetchone=True)
    
    @staticmethod
    def calculate_and_create_bill(reservation_id):
        # Calculate total service charges
        service_total_row = query("SELECT SUM(service_price * quantity) as total FROM reservation_services WHERE reservation_id=?", (reservation_id,), fetchone=True)
        service_total = service_total_row['total'] if service_total_row and service_total_row['total'] is not None else 0
        
        billing = query("SELECT * FROM billing WHERE reservation_id = ?", (reservation_id,), fetchone=True)

        if billing:
            # Simple calculation: initial deposit + service charges
            final_amount = billing['initial_deposit'] + service_total
            execute("UPDATE billing SET final_amount=?, service_charges=?, status=? WHERE billing_id=?", (final_amount, service_total, 'Unpaid', billing['billing_id']))
            return billing['billing_id']
        else:
            # If no billing record exists, create one with 0 deposit
            final_amount = service_total
            bid = execute("INSERT INTO billing (reservation_id, initial_deposit, service_charges, final_amount, amount_paid, status) VALUES (?, ?, ?, ?, ?, ?)", 
                          (reservation_id, 0.0, service_total, final_amount, 0.0, 'Unpaid'))
            return bid

    @staticmethod
    def record_payment(reservation_id, customer_id, amount, method):
        # Update the billing record amount_paid
        billing_row = query("SELECT * FROM billing WHERE reservation_id = ?", (reservation_id,), fetchone=True)
        if not billing_row:
             # Ensure bill exists before recording payment
             CustomerModel.calculate_and_create_bill(reservation_id)
             billing_row = query("SELECT * FROM billing WHERE reservation_id = ?", (reservation_id,), fetchone=True)

        new_paid = billing_row['amount_paid'] + amount
        status = 'Paid' if new_paid >= billing_row['final_amount'] else 'Partial'
        
        execute("UPDATE billing SET amount_paid=?, status=? WHERE billing_id=?", (new_paid, status, billing_row['billing_id']))

        # Record the payment log
        pid = execute("INSERT INTO payment (customer_id, billing_id, amount, payment_method, payment_date) VALUES (?, ?, ?, ?, datetime('now'))", 
                      (customer_id, billing_row['billing_id'], amount, method))
        return pid

    @staticmethod
    def checkout_reservation(reservation_id):
        """Marks the reservation as Checked-out."""
        execute("UPDATE reservation SET status='Checked-out', check_out_date_actual=datetime('now') WHERE reservation_id=?", (reservation_id,))

    @staticmethod
    def get_customer_summary(customer_id):
        """Fetches all reservation, service, and payment history for the dashboard."""
        # 1. Reservations and Services Summary
        services_data = query("""
            SELECT 
                r.reservation_id, 
                r.check_in_date, 
                r.check_out_date, 
                r.num_guests, 
                s.service_name, 
                rs.quantity, 
                rs.service_price
            FROM reservation r
            LEFT JOIN reservation_services rs ON r.reservation_id = rs.reservation_id
            LEFT JOIN service s ON rs.service_id = s.service_id
            WHERE r.customer_id = ?
            ORDER BY r.check_in_date DESC
        """, (customer_id,), fetchall=True)

        # 2. Payments Summary
        payments_data = query("""
            SELECT 
                p.payment_date, 
                p.amount, 
                p.payment_method,
                b.reservation_id,
                b.final_amount,
                b.amount_paid
            FROM payment p
            JOIN billing b ON p.billing_id = b.billing_id
            WHERE p.customer_id = ?
            ORDER BY p.payment_date DESC
        """, (customer_id,), fetchall=True)
        
        return {
            'services_history': services_data,
            'payments_history': payments_data
        }

class RoomModel:

    @staticmethod
    def get_room_capacity(room_id):
        row = query("SELECT room_capacity FROM room WHERE room_id = ?", (room_id,), fetchone=True)
        return row['room_capacity'] if row else 0

    @staticmethod
    def get_available_rooms(check_in, check_out):
        """Finds rooms that are NOT currently booked for any part of the requested period."""
        return query("""
            SELECT * FROM room r
            WHERE r.status = 'available' AND r.room_id NOT IN (
                SELECT reservation.room_id FROM reservation
                WHERE reservation.room_id IS NOT NULL 
                AND reservation.is_cancelled = 0 
                AND (
                    -- New reservation conflicts with existing one
                    (? < check_out_date AND ? >= check_in_date)
                    OR (? <= check_out_date AND ? > check_in_date)
                    OR (? >= check_in_date AND ? <= check_out_date)
                )
            )
        """, (check_out, check_in, check_out, check_in, check_in, check_out), fetchall=True)

    @staticmethod
    def set_room_status(room_id, status):
        """Updates the status of a room (e.g., 'available', 'booked')."""
        execute("UPDATE room SET status=? WHERE room_id=?", (status, room_id))