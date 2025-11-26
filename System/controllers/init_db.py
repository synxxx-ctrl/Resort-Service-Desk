from db import execute, get_conn
import os

if os.path.exists('resort.db'):
    print('resort.db exists. Deleting to apply new schema for Maintenance/Stock tracking...')
    try:
        os.remove('resort.db')
    except PermissionError:
        print("Error: Close the database file/app before running this.")

conn = get_conn()
cur = conn.cursor()

# 1. Create Tables
cur.execute('''CREATE TABLE admin (admin_id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)''')
cur.execute('''CREATE TABLE customer (customer_id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, full_name TEXT, email TEXT, contact_number TEXT)''')
cur.execute('''CREATE TABLE resort_info (id INTEGER PRIMARY KEY AUTOINCREMENT, max_capacity INTEGER)''')
cur.execute('''CREATE TABLE room (room_id INTEGER PRIMARY KEY AUTOINCREMENT, room_number TEXT UNIQUE, room_capacity INTEGER, status TEXT, type TEXT)''')

cur.execute('''CREATE TABLE reservation (
    reservation_id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER, check_in_date TEXT, check_out_date TEXT, 
    check_out_date_actual TEXT, num_guests INTEGER, count_adults INTEGER DEFAULT 0, count_kids INTEGER DEFAULT 0, 
    count_pwd INTEGER DEFAULT 0, count_seniors INTEGER DEFAULT 0, status TEXT, notes TEXT, created_at TEXT, 
    is_cancelled INTEGER DEFAULT 0, room_id INTEGER,
    FOREIGN KEY(customer_id) REFERENCES customer(customer_id), FOREIGN KEY(room_id) REFERENCES room(room_id)
)''')

cur.execute('''CREATE TABLE service (
    service_id INTEGER PRIMARY KEY AUTOINCREMENT, service_name TEXT, description TEXT, base_price REAL, stock_total INTEGER DEFAULT 999
)''')

cur.execute('''CREATE TABLE reservation_services (id INTEGER PRIMARY KEY AUTOINCREMENT, reservation_id INTEGER, service_id INTEGER, quantity INTEGER, service_price REAL, FOREIGN KEY(reservation_id) REFERENCES reservation(reservation_id), FOREIGN KEY(service_id) REFERENCES service(service_id))''')
cur.execute('''CREATE TABLE waitlist (waitlist_id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER, requested_service TEXT, timestamp TEXT, FOREIGN KEY(customer_id) REFERENCES customer(customer_id))''')

cur.execute('''CREATE TABLE billing (
    billing_id INTEGER PRIMARY KEY AUTOINCREMENT, reservation_id INTEGER, initial_deposit REAL DEFAULT 0.0, 
    service_charges REAL DEFAULT 0.0, discount_amount REAL DEFAULT 0.0, compensation REAL DEFAULT 0.0,
    final_amount REAL, amount_paid REAL DEFAULT 0.0, status TEXT, cashier_name TEXT DEFAULT 'Admin Cashier', created_at TEXT, 
    FOREIGN KEY(reservation_id) REFERENCES reservation(reservation_id)
)''')

cur.execute('''CREATE TABLE payment (payment_id INTEGER PRIMARY KEY AUTOINCREMENT, billing_id INTEGER, customer_id INTEGER, payment_method TEXT, amount REAL, payment_date TEXT, FOREIGN KEY(billing_id) REFERENCES billing(billing_id), FOREIGN KEY(customer_id) REFERENCES customer(customer_id))''')
cur.execute('''CREATE TABLE receipt (receipt_id INTEGER PRIMARY KEY AUTOINCREMENT, billing_id INTEGER, receipt_no TEXT, issued_at TEXT, content TEXT, FOREIGN KEY(billing_id) REFERENCES billing(billing_id))''')

# --- UPDATED: Added service_id AND reservation_id to maintenance_logs ---
cur.execute('''CREATE TABLE maintenance_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT, 
    room_id INTEGER, 
    service_id INTEGER, 
    reservation_id INTEGER,
    reported_by_customer_id INTEGER, 
    issue_description TEXT, 
    action_taken TEXT, 
    status TEXT, 
    date_reported TEXT, 
    date_resolved TEXT, 
    FOREIGN KEY(room_id) REFERENCES room(room_id),
    FOREIGN KEY(service_id) REFERENCES service(service_id),
    FOREIGN KEY(reservation_id) REFERENCES reservation(reservation_id)
)''')

# 2. Seed Data
cur.execute('INSERT INTO admin (username, password) VALUES (?, ?)', ('admin', 'admin'))

services = [
    ('Room Fee - Single (1 Pax)', 'Standard single room per night', 1500.0, 999),
    ('Room Fee - Double (2 Pax)', 'Standard double room per night', 2500.0, 999),
    ('Room Fee - Family (4 Pax)', 'Family room per night', 4500.0, 999),
    ('Room Fee - Suite (6 Pax)', 'Luxury suite per night', 7000.0, 999),
    ('Cottage Rental (10 Pax)', 'Large group cottage rental', 10000.0, 999),
    ('Meal: Solo (1 Pax)', 'Set meal for 1 person', 350.0, 999),
    ('Meal: Couple (2 Pax)', 'Set meal for 2 people', 600.0, 999),
    ('Meal: Family (4-6 Pax)', 'Bundle for 4-6 people', 1500.0, 999),
    ('Meal: Feast (6-10 Pax)', 'Bundle for 6-10 people', 2800.0, 999),
    
    # LIMITED STOCK AMENITIES
    ('Karaoke Rental', 'Per hour/session use', 500.0, 5),
    ('Pool Access', 'Pool day pass per pax', 250.0, 50),
    ('Spa Session', '60-min spa per pax', 800.0, 5),
    ('Banana Boat', 'Per ride per group', 1500.0, 3),
    ('Jetski', 'Per 15-min ride', 2000.0, 3),
    ('Extra Bed', 'Folding bed with linens', 500.0, 10)
]
cur.executemany('INSERT INTO service (service_name, description, base_price, stock_total) VALUES (?, ?, ?, ?)', services)

cur.execute('INSERT INTO resort_info (max_capacity) VALUES (?)', (100,))

rooms_data = [
    ('Single 101', 1, 'available', 'Room'), ('Single 102', 1, 'available', 'Room'),
    ('Double 201', 2, 'available', 'Room'), ('Double 202', 2, 'available', 'Room'), ('Double 203', 2, 'available', 'Room'), ('Double 204', 2, 'available', 'Room'),
    ('Family 301', 4, 'available', 'Room'), ('Family 302', 4, 'available', 'Room'), ('Family 303', 4, 'available', 'Room'), ('Family 304', 4, 'available', 'Room'),
    ('Suite 401', 6, 'available', 'Room'), ('Suite 402', 6, 'available', 'Room'), ('Suite 403', 6, 'available', 'Room'), ('Suite 404', 6, 'available', 'Room'),
    ('Cottage 01', 10, 'available', 'Cottage'), ('Cottage 02', 10, 'available', 'Cottage'), ('Cottage 03', 10, 'available', 'Cottage'), ('Cottage 04', 10, 'available', 'Cottage'), ('Cottage 05', 10, 'available', 'Cottage')
]
cur.executemany('INSERT INTO room (room_number, room_capacity, status, type) VALUES (?, ?, ?, ?)', rooms_data)

conn.commit()
conn.close()
print('resort.db recreated successfully.')