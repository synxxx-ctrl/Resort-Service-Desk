from db import execute, get_conn
import os

if os.path.exists('resort.db'):
    print('resort.db exists. Deleting to apply new "Choosy" Package schema...')
    try:
        os.remove('resort.db')
    except PermissionError:
        print("Error: Close the database file/app before running this.")

conn = get_conn()
cur = conn.cursor()

# 1. Create Tables
cur.execute('''CREATE TABLE admin (admin_id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)''')
cur.execute('''CREATE TABLE customer (customer_id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, full_name TEXT, email TEXT, contact_number TEXT)''')

cur.execute('''CREATE TABLE resort_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    max_capacity INTEGER,
    fee_adult REAL DEFAULT 150.0,
    fee_teen REAL DEFAULT 100.0,
    fee_kid REAL DEFAULT 0.0
)''')

cur.execute('''CREATE TABLE room (room_id INTEGER PRIMARY KEY AUTOINCREMENT, room_number TEXT UNIQUE, room_capacity INTEGER, status TEXT, type TEXT)''')

cur.execute('''CREATE TABLE reservation (
    reservation_id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER, check_in_date TEXT, check_out_date TEXT, 
    check_out_date_actual TEXT, num_guests INTEGER, 
    count_adults INTEGER DEFAULT 0, count_teens INTEGER DEFAULT 0, count_kids INTEGER DEFAULT 0, 
    count_pwd INTEGER DEFAULT 0, count_seniors INTEGER DEFAULT 0, 
    status TEXT, notes TEXT, created_at TEXT, 
    is_cancelled INTEGER DEFAULT 0, room_id INTEGER,
    FOREIGN KEY(customer_id) REFERENCES customer(customer_id), FOREIGN KEY(room_id) REFERENCES room(room_id)
)''')

# UPDATED: Added linked_room_type and linked_room_capacity
cur.execute('''CREATE TABLE service (
    service_id INTEGER PRIMARY KEY AUTOINCREMENT, 
    service_name TEXT, 
    description TEXT, 
    base_price REAL, 
    stock_total INTEGER DEFAULT 999, 
    category TEXT DEFAULT 'Add-on',
    linked_room_type TEXT, 
    linked_room_capacity INTEGER
)''')

cur.execute('''CREATE TABLE reservation_services (id INTEGER PRIMARY KEY AUTOINCREMENT, reservation_id INTEGER, service_id INTEGER, quantity INTEGER, service_price REAL, FOREIGN KEY(reservation_id) REFERENCES reservation(reservation_id), FOREIGN KEY(service_id) REFERENCES service(service_id))''')

cur.execute('''CREATE TABLE billing (
    billing_id INTEGER PRIMARY KEY AUTOINCREMENT, reservation_id INTEGER, initial_deposit REAL DEFAULT 0.0, 
    service_charges REAL DEFAULT 0.0, discount_amount REAL DEFAULT 0.0, compensation REAL DEFAULT 0.0,
    final_amount REAL, amount_paid REAL DEFAULT 0.0, status TEXT, cashier_name TEXT DEFAULT 'Admin Cashier', created_at TEXT, 
    FOREIGN KEY(reservation_id) REFERENCES reservation(reservation_id)
)''')

cur.execute('''CREATE TABLE payment (payment_id INTEGER PRIMARY KEY AUTOINCREMENT, billing_id INTEGER, customer_id INTEGER, payment_method TEXT, amount REAL, payment_date TEXT, FOREIGN KEY(billing_id) REFERENCES billing(billing_id), FOREIGN KEY(customer_id) REFERENCES customer(customer_id))''')
cur.execute('''CREATE TABLE maintenance_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT, room_id INTEGER, service_id INTEGER, reservation_id INTEGER,
    reported_by_customer_id INTEGER, issue_description TEXT, action_taken TEXT, status TEXT, date_reported TEXT, date_resolved TEXT, 
    FOREIGN KEY(room_id) REFERENCES room(room_id), FOREIGN KEY(service_id) REFERENCES service(service_id), FOREIGN KEY(reservation_id) REFERENCES reservation(reservation_id)
)''')

# 2. Seed Data
cur.execute('INSERT INTO admin (username, password) VALUES (?, ?)', ('admin', 'admin'))

services = [
    # ROOM FEES (Hidden, used for backend logic)
    ('Room Fee - Single (1 Pax)', 'Standard single room', 1500.0, 999, 'Room', None, None),
    ('Room Fee - Double (2 Pax)', 'Standard double room', 2500.0, 999, 'Room', None, None),
    ('Room Fee - Family (4 Pax)', 'Family room', 4500.0, 999, 'Room', None, None),
    ('Room Fee - Suite (6 Pax)', 'Luxury suite', 7000.0, 999, 'Room', None, None),
    ('Cottage Rental (10 Pax)', 'Large group cottage', 1000.0, 999, 'Cottage', None, None),
    
    # ==========================
    #        PACKAGES
    # ==========================

    # --- TIER 1: DAY TOUR / COTTAGE PACKAGES ---
    # Choice A: Just chill with friends (Karaoke focus)
    ('Pkg: Barkada Chill (Cottage)', 'Inc: Cottage + Karaoke (2hrs) + Beer Bucket', 1800.0, 999, 'Package', 'Cottage', 10),
    # Choice B: Action packed (Water Sports focus)
    ('Pkg: Water Adventure (Cottage)', 'Inc: Cottage + Banana Boat + Jetski (15m)', 4000.0, 999, 'Package', 'Cottage', 10),

    # --- TIER 2: COUPLE / DOUBLE ROOM PACKAGES ---
    # Choice A: Relaxing
    ('Pkg: Couple Relax (Double Room)', 'Inc: Double Room + 2 Spa Sessions + Breakfast', 3800.0, 999, 'Package', 'Room', 2),
    # Choice B: Thrill Seeking
    ('Pkg: Couple Thrill (Double Room)', 'Inc: Double Room + Jetski (15m) + Breakfast', 4500.0, 999, 'Package', 'Room', 2),

    # --- TIER 3: FAMILY / GROUP ROOM PACKAGES ---
    # Choice A: Moderate Fun
    ('Pkg: Family Fun (Family Room)', 'Inc: Family Room (4pax) + Banana Boat + Karaoke', 6500.0, 999, 'Package', 'Room', 4),
    # Choice B: All-in / The "Grand" Package
    ('Pkg: The Grand Experience (Suite)', 'Inc: Suite (6pax) + Jetski + Banana Boat + Karaoke + 6 Meals', 12000.0, 999, 'Package', 'Room', 6),


    # ==========================
    #       A LA CARTE
    # ==========================
    ('Karaoke Rental', 'Per hour', 500.0, 5, 'Amenity', None, None),
    ('Pool Access', 'Per person', 250.0, 50, 'Amenity', None, None),
    ('Spa Session', '60-min massage', 800.0, 5, 'Amenity', None, None),
    ('Banana Boat', 'Per ride', 1500.0, 3, 'Activity', None, None),
    ('Jetski', 'Per 15-min', 2000.0, 3, 'Activity', None, None),
    ('Extra Bed', 'Foam + Linens', 500.0, 10, 'Amenity', None, None),

    # --- FOOD (Restaurant Menu) ---
    ('Silog Meal (Solo)', 'Rice + Egg + Meat', 150.0, 999, 'Food', None, None),
    ('Seafood Platter', 'Shrimp, Squid, Crab', 1200.0, 999, 'Food', None, None),
    ('Boodle Fight (Group)', 'Rice + Mixed Viands (4-6pax)', 1800.0, 999, 'Food', None, None),
    ('Fruit Shake', 'Mango/Watermelon', 120.0, 999, 'Food', None, None),
    ('Beer Bucket', '6 Bottles', 500.0, 999, 'Food', None, None)
]

cur.executemany('INSERT INTO service (service_name, description, base_price, stock_total, category, linked_room_type, linked_room_capacity) VALUES (?, ?, ?, ?, ?, ?, ?)', services)

cur.execute('INSERT INTO resort_info (max_capacity, fee_adult, fee_teen, fee_kid) VALUES (?, ?, ?, ?)', (100, 150.0, 100.0, 0.0))

rooms_data = [
    ('Single 101', 1, 'available', 'Room'), ('Single 102', 1, 'available', 'Room'),
    ('Double 201', 2, 'available', 'Room'), ('Double 202', 2, 'available', 'Room'), ('Double 203', 2, 'available', 'Room'),
    ('Family 301', 4, 'available', 'Room'), ('Family 302', 4, 'available', 'Room'),
    ('Suite 401', 6, 'available', 'Room'),
    ('Cottage 01', 10, 'available', 'Cottage'), ('Cottage 02', 10, 'available', 'Cottage'), ('Cottage 03', 10, 'available', 'Cottage')
]
cur.executemany('INSERT INTO room (room_number, room_capacity, status, type) VALUES (?, ?, ?, ?)', rooms_data)

conn.commit()
conn.close()
print('DB Re-initialized: Packages split into Tiers (Chill vs Adventure).')