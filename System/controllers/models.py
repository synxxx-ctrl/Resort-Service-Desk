from db import query, execute
from datetime import datetime

class AdminModel:
    @staticmethod
    def check_login(username, password):
        row = query("SELECT * FROM admin WHERE username = ?", (username,), fetchone=True)
        if not row: return False
        return row['password'] == password

    @staticmethod
    def change_credentials(admin_id, new_username, new_password):
        execute("UPDATE admin SET username=?, password=? WHERE admin_id=?", (new_username, new_password, admin_id))

class CustomerModel:
    @staticmethod
    def create_customer(username, full_name, email, contact_number):
        return execute("INSERT INTO customer (username, full_name, email, contact_number) VALUES (?, ?, ?, ?)", (username, full_name, email, contact_number))

    @staticmethod
    def get_customer_by_id(customer_id):
        return query("SELECT * FROM customer WHERE customer_id=?", (customer_id,), fetchone=True)
    
    @staticmethod
    def calculate_and_create_bill(reservation_id):
        res = query("SELECT check_in_date, check_out_date FROM reservation WHERE reservation_id=?", (reservation_id,), fetchone=True)
        nights = 1
        if res:
            try:
                s_in = res['check_in_date'].replace('T', ' ')
                s_out = res['check_out_date'].replace('T', ' ')
                fmt = "%Y-%m-%d %H:%M:%S" if ":" in s_in else "%Y-%m-%d"
                delta = (datetime.strptime(s_out, fmt) - datetime.strptime(s_in, fmt)).days
                nights = delta if delta > 0 else 1
            except: nights = 1

        service_total_row = query("SELECT SUM(service_price * quantity) as total FROM reservation_services WHERE reservation_id=?", (reservation_id,), fetchone=True)
        base_total = service_total_row['total'] if service_total_row and service_total_row['total'] is not None else 0.0
        service_total = base_total * nights
        
        billing = query("SELECT * FROM billing WHERE reservation_id = ?", (reservation_id,), fetchone=True)

        if billing:
            discount = billing['discount_amount'] if billing['discount_amount'] else 0.0
            comp = billing['compensation'] if billing['compensation'] else 0.0
            paid = billing['amount_paid'] if billing['amount_paid'] else 0.0
            
            final_amount = service_total - discount - comp
            if final_amount < 0: final_amount = 0.0

            status = 'Paid' if paid >= final_amount else 'Unpaid'
            if paid > 0 and paid < final_amount: status = 'Partial'

            execute("UPDATE billing SET service_charges=?, final_amount=?, status=? WHERE billing_id=?", 
                    (service_total, final_amount, status, billing['billing_id']))
            return billing['billing_id']
        else:
            execute("INSERT INTO billing (reservation_id, final_amount, service_charges, amount_paid, status, cashier_name, created_at) VALUES (?, ?, ?, 0.0, 'Unpaid', 'Admin Cashier', datetime('now'))", 
                          (reservation_id, service_total, service_total))
            return None

    @staticmethod
    def record_payment(reservation_id, customer_id, amount, method):
        CustomerModel.calculate_and_create_bill(reservation_id)
        billing_row = query("SELECT * FROM billing WHERE reservation_id = ?", (reservation_id,), fetchone=True)
        current_paid = billing_row['amount_paid'] or 0.0
        final_amount = billing_row['final_amount'] or 0.0
        new_paid = current_paid + amount
        status = 'Paid' if new_paid >= final_amount else 'Partial'
        execute("UPDATE billing SET amount_paid=?, status=? WHERE billing_id=?", (new_paid, status, billing_row['billing_id']))
        return execute("INSERT INTO payment (customer_id, billing_id, amount, payment_method, payment_date) VALUES (?, ?, ?, ?, datetime('now'))", (customer_id, billing_row['billing_id'], amount, method))

    @staticmethod
    def checkout_reservation(reservation_id):
        execute("UPDATE reservation SET status='Checked-out', check_out_date_actual=datetime('now') WHERE reservation_id=?", (reservation_id,))

    @staticmethod
    def get_customer_summary(customer_id):
        services_data = query("""SELECT r.reservation_id, r.check_in_date, r.check_out_date, r.status, s.service_name, rs.quantity, rs.service_price
            FROM reservation r LEFT JOIN reservation_services rs ON r.reservation_id = rs.reservation_id
            LEFT JOIN service s ON rs.service_id = s.service_id WHERE r.customer_id = ? ORDER BY r.check_in_date DESC""", (customer_id,), fetchall=True)
        payments_data = query("""SELECT p.payment_date, p.amount, p.payment_method, b.reservation_id, b.final_amount, b.amount_paid
            FROM payment p JOIN billing b ON p.billing_id = b.billing_id WHERE p.customer_id = ? ORDER BY p.payment_date DESC""", (customer_id,), fetchall=True)
        return {'services_history': services_data, 'payments_history': payments_data}

class RoomModel:
    @staticmethod
    def get_room_capacity(room_id):
        row = query("SELECT room_capacity FROM room WHERE room_id = ?", (room_id,), fetchone=True)
        return row['room_capacity'] if row else 0

    @staticmethod
    def get_available_rooms(check_in, check_out):
        return query("""SELECT * FROM room r WHERE r.status = 'available' AND r.room_id NOT IN (
                SELECT reservation.room_id FROM reservation WHERE reservation.room_id IS NOT NULL AND reservation.is_cancelled = 0 
                AND reservation.status NOT IN ('Checked-out', 'Cancelled') AND (
                    (? < check_out_date AND ? >= check_in_date) OR (? <= check_out_date AND ? > check_in_date) OR (? >= check_in_date AND ? <= check_out_date)
                ))""", (check_out, check_in, check_out, check_in, check_in, check_out), fetchall=True)

    @staticmethod
    def set_room_status(room_id, status):
        execute("UPDATE room SET status=? WHERE room_id=?", (status, room_id))

class MaintenanceModel:
    @staticmethod
    def report_issue(room_id, customer_id, issue, action):
        execute("""INSERT INTO maintenance_logs (room_id, reported_by_customer_id, issue_description, action_taken, status, date_reported) 
                   VALUES (?, ?, ?, ?, 'Pending', datetime('now'))""", (room_id, customer_id, issue, action))
        if room_id: RoomModel.set_room_status(room_id, 'maintenance')

    @staticmethod
    def resolve_issue(log_id):
        row = query("SELECT room_id FROM maintenance_logs WHERE log_id=?", (log_id,), fetchone=True)
        if row:
            execute("UPDATE maintenance_logs SET status='Resolved', date_resolved=datetime('now') WHERE log_id=?", (log_id,))
            if row['room_id']: RoomModel.set_room_status(row['room_id'], 'available')

class AmenityModel:
    @staticmethod
    def get_available_stock(service_id, stock_total):
        # Calculate used stock based on active reservations
        active_usage = query("""
            SELECT SUM(rs.quantity) as used_count
            FROM reservation_services rs
            JOIN reservation r ON rs.reservation_id = r.reservation_id
            WHERE rs.service_id = ? AND (r.status = 'Checked-in' OR r.status = 'Pending')
        """, (service_id,), fetchone=True)
        
        used = active_usage['used_count'] if active_usage and active_usage['used_count'] else 0
        available = stock_total - used
        return max(0, available)

class ResortModel:
    @staticmethod
    def get_max_capacity():
        row = query("SELECT max_capacity FROM resort_info LIMIT 1", fetchone=True)
        return row['max_capacity'] if row else 100

    @staticmethod
    def check_capacity_availability(check_in_str, check_out_str, new_guests):
        max_cap = ResortModel.get_max_capacity()
        row = query("""SELECT SUM(num_guests) as current_load FROM reservation WHERE status NOT IN ('Checked-out', 'Cancelled') AND (check_in_date < ? AND check_out_date > ?)""", (check_out_str, check_in_str), fetchone=True)
        current_load = row['current_load'] if row and row['current_load'] else 0
        if (current_load + new_guests) > max_cap: return False, max_cap, current_load
        return True, max_cap, current_load