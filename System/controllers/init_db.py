from db import execute, get_conn
import os

if os.path.exists('resort.db'):
    print('resort.db already exists - skipping creation. Delete it to recreate.')
else:
    conn = get_conn()
    cur = conn.cursor()

    # admin table
    cur.execute('''CREATE TABLE admin (
        admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )''')

    # customer table
    cur.execute('''CREATE TABLE customer (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        full_name TEXT,
        email TEXT,
        contact_number TEXT
    )''')

    # resort info (capacity)
    cur.execute('''CREATE TABLE resort_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        max_capacity INTEGER
    )''')

    # rooms
    cur.execute('''CREATE TABLE room (
        room_id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_number TEXT UNIQUE,
        room_capacity INTEGER,
        status TEXT
    )''')

    # reservation table
    cur.execute('''CREATE TABLE reservation (
        reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        check_in_date TEXT,
        check_out_date TEXT,
        num_guests INTEGER,
        status TEXT,
        notes TEXT,
        created_at TEXT,
        is_cancelled INTEGER DEFAULT 0,
        room_id INTEGER,
        FOREIGN KEY(customer_id) REFERENCES customer(customer_id),
        FOREIGN KEY(room_id) REFERENCES room(room_id)
    )''')

    # service table
    cur.execute('''CREATE TABLE service (
        service_id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_name TEXT,
        description TEXT,
        base_price REAL
    )''')

    # reservation_services linking table
    cur.execute('''CREATE TABLE reservation_services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reservation_id INTEGER,
        service_id INTEGER,
        quantity INTEGER,
        service_price REAL,
        FOREIGN KEY(reservation_id) REFERENCES reservation(reservation_id),
        FOREIGN KEY(service_id) REFERENCES service(service_id)
    )''')

    # waitlist table
    cur.execute('''CREATE TABLE waitlist (
        waitlist_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        requested_service TEXT,
        timestamp TEXT,
        FOREIGN KEY(customer_id) REFERENCES customer(customer_id)
    )''')

    # billing table
    cur.execute('''CREATE TABLE billing (
        billing_id INTEGER PRIMARY KEY AUTOINCREMENT,
        reservation_id INTEGER,
        final_amount REAL,
        status TEXT,
        created_at TEXT,
        FOREIGN KEY(reservation_id) REFERENCES reservation(reservation_id)
    )''')

    # payment table
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

    # receipt table
    cur.execute('''CREATE TABLE receipt (
        receipt_id INTEGER PRIMARY KEY AUTOINCREMENT,
        billing_id INTEGER,
        receipt_no TEXT,
        issued_at TEXT,
        content TEXT,
        FOREIGN KEY(billing_id) REFERENCES billing(billing_id)
    )''')

    # Seed admin
    cur.execute('INSERT INTO admin (username, password) VALUES (?, ?)', ('admin', 'admin'))

    # Seed services
    services = [
        ('Room - Standard','Standard room per night', 2500.0),
        ('Beach Cottage','Private cottage rental', 1200.0),
        ('Pool Access','Pool day pass per pax', 250.0),
        ('Restaurant - Set Meal','Set meal per pax', 350.0),
        ('Spa Session','60-min spa per pax', 800.0),
        ('Banana Boat','Per ride per group', 1500.0),
        ('Jetski','Per 15-min ride', 2000.0)
    ]
    cur.executemany('INSERT INTO service (service_name, description, base_price) VALUES (?, ?, ?)', services)

    # Seed resort capacity
    cur.execute('INSERT INTO resort_info (max_capacity) VALUES (?)', (50,))  # Example: max 50 guests

    # Seed rooms
    rooms = [
        ('R101', 2, 'available'),
        ('R102', 2, 'available'),
        ('R201', 4, 'available'),
        ('R202', 4, 'available'),
        ('VIP1', 6, 'available')
    ]
    cur.executemany('INSERT INTO room (room_number, room_capacity, status) VALUES (?, ?, ?)', rooms)

    conn.commit()
    conn.close()
    print('resort.db created and seeded with sample data.')
