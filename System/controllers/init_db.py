from db import execute, get_conn
import os

# --- IMPORTANT: DELETE OLD DB FILE BEFORE RUNNING THIS TO RESET DATA ---
if os.path.exists('resort.db'):
    print('resort.db already exists - skipping creation. Delete the file to recreate with new rooms and pricing.')
else:
    conn = get_conn()
    cur = conn.cursor()

    # 1. Create Tables
    cur.execute('''CREATE TABLE admin (
        admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )''')

    cur.execute('''CREATE TABLE customer (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        full_name TEXT,
        email TEXT,
        contact_number TEXT
    )''')

    cur.execute('''CREATE TABLE resort_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        max_capacity INTEGER
    )''')

    cur.execute('''CREATE TABLE room (
        room_id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_number TEXT UNIQUE,
        room_capacity INTEGER,
        status TEXT,
        type TEXT 
    )''')

    cur.execute('''CREATE TABLE reservation (
        reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        check_in_date TEXT,
        check_out_date TEXT,
        check_out_date_actual TEXT, 
        num_guests INTEGER,
        status TEXT,
        notes TEXT,
        created_at TEXT,
        is_cancelled INTEGER DEFAULT 0,
        room_id INTEGER,
        FOREIGN KEY(customer_id) REFERENCES customer(customer_id),
        FOREIGN KEY(room_id) REFERENCES room(room_id)
    )''')

    cur.execute('''CREATE TABLE service (
        service_id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_name TEXT,
        description TEXT,
        base_price REAL
    )''')

    cur.execute('''CREATE TABLE reservation_services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reservation_id INTEGER,
        service_id INTEGER,
        quantity INTEGER,
        service_price REAL,
        FOREIGN KEY(reservation_id) REFERENCES reservation(reservation_id),
        FOREIGN KEY(service_id) REFERENCES service(service_id)
    )''')

    cur.execute('''CREATE TABLE waitlist (
        waitlist_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        requested_service TEXT,
        timestamp TEXT,
        FOREIGN KEY(customer_id) REFERENCES customer(customer_id)
    )''')

    cur.execute('''CREATE TABLE billing (
        billing_id INTEGER PRIMARY KEY AUTOINCREMENT,
        reservation_id INTEGER,
        initial_deposit REAL DEFAULT 0.0, 
        service_charges REAL DEFAULT 0.0, 
        final_amount REAL,
        amount_paid REAL DEFAULT 0.0,
        status TEXT,
        created_at TEXT,
        FOREIGN KEY(reservation_id) REFERENCES reservation(reservation_id)
    )''')

    cur.execute('''CREATE TABLE payment (
        payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        billing_id INTEGER,
        customer_id INTEGER,
        payment_method TEXT,
        amount REAL,
        payment_date TEXT,
        FOREIGN KEY(billing_id) REFERENCES billing(billing_id),
        FOREIGN KEY(customer_id) REFERENCES customer(customer_id)
    )''')
    
    cur.execute('''CREATE TABLE receipt (
        receipt_id INTEGER PRIMARY KEY AUTOINCREMENT,
        billing_id INTEGER,
        receipt_no TEXT,
        issued_at TEXT,
        content TEXT,
        FOREIGN KEY(billing_id) REFERENCES billing(billing_id)
    )''')

    # 2. Seed Admin
    cur.execute('INSERT INTO admin (username, password) VALUES (?, ?)', ('admin', 'admin'))

    # 3. Seed Services with SPECIFIC ROOM PRICING
    services = [
        # Accommodation Fees
        ('Room Fee - Single (1 Pax)', 'Standard single room per night', 1500.0),
        ('Room Fee - Double (2 Pax)', 'Standard double room per night', 2500.0),
        ('Room Fee - Family (4 Pax)', 'Family room per night', 4500.0),
        ('Room Fee - Suite (6 Pax)', 'Luxury suite per night', 7000.0),
        ('Cottage Rental (10 Pax)', 'Large group cottage rental', 10000.0),
        
        # Amenities / Extras
        ('Pool Access', 'Pool day pass per pax', 250.0),
        ('Restaurant - Set Meal', 'Set meal per pax', 350.0),
        ('Spa Session', '60-min spa per pax', 800.0),
        ('Banana Boat', 'Per ride per group', 1500.0),
        ('Jetski', 'Per 15-min ride', 2000.0),
        ('Extra Bed', 'Folding bed with linens', 500.0)
    ]
    cur.executemany('INSERT INTO service (service_name, description, base_price) VALUES (?, ?, ?)', services)

    # 4. Seed Resort Info (Max Capacity = 100)
    cur.execute('INSERT INTO resort_info (max_capacity) VALUES (?)', (100,))

    # 5. Seed Rooms & Cottages (Exact 100 Pax Configuration)
    rooms_data = []

    # A. Single Rooms (2 rooms, 1 pax) -> Total 2 pax
    rooms_data.append(('Single 101', 1, 'available', 'Room'))
    rooms_data.append(('Single 102', 1, 'available', 'Room'))

    # B. Double Rooms (4 rooms, 2 pax) -> Total 8 pax
    rooms_data.append(('Double 201', 2, 'available', 'Room'))
    rooms_data.append(('Double 202', 2, 'available', 'Room'))
    rooms_data.append(('Double 203', 2, 'available', 'Room'))
    rooms_data.append(('Double 204', 2, 'available', 'Room'))

    # C. Family Rooms (4 rooms, 4 pax) -> Total 16 pax
    rooms_data.append(('Family 301', 4, 'available', 'Room'))
    rooms_data.append(('Family 302', 4, 'available', 'Room'))
    rooms_data.append(('Family 303', 4, 'available', 'Room'))
    rooms_data.append(('Family 304', 4, 'available', 'Room'))

    # D. Suites/Villas (4 rooms, 6 pax) -> Total 24 pax
    rooms_data.append(('Suite 401', 6, 'available', 'Room'))
    rooms_data.append(('Suite 402', 6, 'available', 'Room'))
    rooms_data.append(('Suite 403', 6, 'available', 'Room'))
    rooms_data.append(('Suite 404', 6, 'available', 'Room'))

    # E. Cottages (5 cottages, 10 pax each) -> Total 50 pax
    rooms_data.append(('Cottage 01', 10, 'available', 'Cottage'))
    rooms_data.append(('Cottage 02', 10, 'available', 'Cottage'))
    rooms_data.append(('Cottage 03', 10, 'available', 'Cottage'))
    rooms_data.append(('Cottage 04', 10, 'available', 'Cottage'))
    rooms_data.append(('Cottage 05', 10, 'available', 'Cottage'))

    # Insert into DB
    cur.executemany('INSERT INTO room (room_number, room_capacity, status, type) VALUES (?, ?, ?, ?)', rooms_data)

    conn.commit()
    conn.close()
    print('resort.db created with specific Room Pricing and 100 Pax Capacity.')