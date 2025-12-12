BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS admin (admin_id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT);
CREATE TABLE IF NOT EXISTS billing (
    billing_id INTEGER PRIMARY KEY AUTOINCREMENT, reservation_id INTEGER, initial_deposit REAL DEFAULT 0.0, 
    service_charges REAL DEFAULT 0.0, discount_amount REAL DEFAULT 0.0, compensation REAL DEFAULT 0.0,
    final_amount REAL, amount_paid REAL DEFAULT 0.0, status TEXT, cashier_name TEXT DEFAULT 'Admin Cashier', created_at TEXT, 
    FOREIGN KEY(reservation_id) REFERENCES reservation(reservation_id)
);
CREATE TABLE IF NOT EXISTS customer (customer_id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, full_name TEXT, email TEXT, contact_number TEXT);
CREATE TABLE IF NOT EXISTS maintenance_logs (
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
);
CREATE TABLE IF NOT EXISTS payment (payment_id INTEGER PRIMARY KEY AUTOINCREMENT, billing_id INTEGER, customer_id INTEGER, payment_method TEXT, amount REAL, payment_date TEXT, FOREIGN KEY(billing_id) REFERENCES billing(billing_id), FOREIGN KEY(customer_id) REFERENCES customer(customer_id));
CREATE TABLE IF NOT EXISTS receipt (receipt_id INTEGER PRIMARY KEY AUTOINCREMENT, billing_id INTEGER, receipt_no TEXT, issued_at TEXT, content TEXT, FOREIGN KEY(billing_id) REFERENCES billing(billing_id));
CREATE TABLE IF NOT EXISTS reservation (
    reservation_id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER, check_in_date TEXT, check_out_date TEXT, 
    check_out_date_actual TEXT, num_guests INTEGER, count_adults INTEGER DEFAULT 0, count_kids INTEGER DEFAULT 0, 
    count_pwd INTEGER DEFAULT 0, count_seniors INTEGER DEFAULT 0, status TEXT, notes TEXT, created_at TEXT, 
    is_cancelled INTEGER DEFAULT 0, room_id INTEGER,
    FOREIGN KEY(customer_id) REFERENCES customer(customer_id), FOREIGN KEY(room_id) REFERENCES room(room_id)
);
CREATE TABLE IF NOT EXISTS reservation_services (id INTEGER PRIMARY KEY AUTOINCREMENT, reservation_id INTEGER, service_id INTEGER, quantity INTEGER, service_price REAL, FOREIGN KEY(reservation_id) REFERENCES reservation(reservation_id), FOREIGN KEY(service_id) REFERENCES service(service_id));
CREATE TABLE IF NOT EXISTS resort_info (id INTEGER PRIMARY KEY AUTOINCREMENT, max_capacity INTEGER);
CREATE TABLE IF NOT EXISTS room (room_id INTEGER PRIMARY KEY AUTOINCREMENT, room_number TEXT UNIQUE, room_capacity INTEGER, status TEXT, type TEXT);
CREATE TABLE IF NOT EXISTS service (
    service_id INTEGER PRIMARY KEY AUTOINCREMENT, service_name TEXT, description TEXT, base_price REAL, stock_total INTEGER DEFAULT 999
);
CREATE TABLE IF NOT EXISTS waitlist (waitlist_id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER, requested_service TEXT, timestamp TEXT, FOREIGN KEY(customer_id) REFERENCES customer(customer_id));
INSERT INTO "admin" ("admin_id","username","password") VALUES (1,'admin','admin');
INSERT INTO "billing" ("billing_id","reservation_id","initial_deposit","service_charges","discount_amount","compensation","final_amount","amount_paid","status","cashier_name","created_at") VALUES (1,1,0.0,4500.0,300.0,0.0,4200.0,4200.0,'Paid','Admin Cashier','2025-11-27 10:02:42'),
 (2,2,0.0,11000.0,550.0,0.0,10450.0,10450.0,'Paid','Admin Cashier','2025-11-27 10:03:40'),
 (3,3,0.0,25200.0,0.0,0.0,25200.0,25200.0,'Paid','Admin Cashier','2025-11-27 10:06:19'),
 (4,4,0.0,10500.0,2100.0,0.0,8400.0,8400.0,'Paid','Admin Cashier','2025-11-27 10:33:15'),
 (5,5,0.0,2500.0,0.0,0.0,2500.0,0.0,'Unpaid','Admin Cashier','2025-11-27 10:40:49');
INSERT INTO "customer" ("customer_id","username","full_name","email","contact_number") VALUES (1,'6738','marc','marc@gmail.com','09166166707'),
 (2,'1810','Tristan','tsa@gmail.com','09701482232'),
 (3,'4492','Clar','clr@gmail.com','09212375812'),
 (4,'2128','Admin','admin@gmail.com','0921853153');
INSERT INTO "maintenance_logs" ("log_id","room_id","service_id","reservation_id","reported_by_customer_id","issue_description","action_taken","status","date_reported","date_resolved") VALUES (1,NULL,10,NULL,3,'Karaoke Rental: Walang Mic','Swapped to Karaoke Rental','Resolved','2025-11-27 02:35:09','2025-11-27 02:35:48');
INSERT INTO "payment" ("payment_id","billing_id","customer_id","payment_method","amount","payment_date") VALUES (1,1,1,'Cash',4200.0,'2025-11-27 10:02:42'),
 (2,3,3,'Cash',20000.0,'2025-11-27 10:06:19'),
 (3,2,2,'Cash',10450.0,'2025-11-27 02:08:34'),
 (4,4,4,'Cash',8400.0,'2025-11-27 10:33:15'),
 (5,3,3,'Cash',5200.0,'2025-11-27 02:37:38');
INSERT INTO "reservation" ("reservation_id","customer_id","check_in_date","check_out_date","check_out_date_actual","num_guests","count_adults","count_kids","count_pwd","count_seniors","status","notes","created_at","is_cancelled","room_id") VALUES (1,1,'2025-11-27T00:00:00','2025-11-28T00:00:00',NULL,3,1,1,1,0,'Checked-in','','2025-11-27 10:02:42',0,7),
 (2,2,'2025-11-27T01:00:00','2025-11-27T13:00:00','2025-11-27 02:08:34',4,1,2,0,1,'Checked-out','','2025-11-27 10:03:40',0,15),
 (3,3,'2025-11-27T00:00:00','2025-12-06T00:00:00','2025-11-27 02:37:38',1,1,0,0,0,'Checked-out','','2025-11-27 10:06:19',0,1),
 (4,4,'2025-11-27T00:00:00','2025-11-28T00:00:00','2025-11-27 02:33:33',10,0,0,10,0,'Checked-out','','2025-11-27 10:33:15',0,16),
 (5,4,'2025-11-27T00:00:00','2025-11-28T00:00:00',NULL,1,1,0,0,0,'Checked-in','','2025-11-27 10:40:49',0,3);
INSERT INTO "reservation_services" ("id","reservation_id","service_id","quantity","service_price") VALUES (1,1,3,1,4500.0),
 (2,2,5,1,10000.0),
 (3,2,10,1,500.0),
 (4,2,15,1,500.0),
 (5,3,1,1,1500.0),
 (6,3,10,1,500.0),
 (7,3,12,1,800.0),
 (8,4,5,1,10000.0),
 (9,4,10,1,500.0),
 (10,5,2,1,2500.0);
INSERT INTO "resort_info" ("id","max_capacity") VALUES (1,100);
INSERT INTO "room" ("room_id","room_number","room_capacity","status","type") VALUES (1,'Single 101',1,'available','Room'),
 (2,'Single 102',1,'available','Room'),
 (3,'Double 201',2,'occupied','Room'),
 (4,'Double 202',2,'available','Room'),
 (5,'Double 203',2,'available','Room'),
 (6,'Double 204',2,'available','Room'),
 (7,'Family 301',4,'occupied','Room'),
 (8,'Family 302',4,'available','Room'),
 (9,'Family 303',4,'available','Room'),
 (10,'Family 304',4,'available','Room'),
 (11,'Suite 401',6,'available','Room'),
 (12,'Suite 402',6,'available','Room'),
 (13,'Suite 403',6,'available','Room'),
 (14,'Suite 404',6,'available','Room'),
 (15,'Cottage 01',10,'cleaning','Cottage'),
 (16,'Cottage 02',10,'cleaning','Cottage'),
 (17,'Cottage 03',10,'available','Cottage'),
 (18,'Cottage 04',10,'available','Cottage'),
 (19,'Cottage 05',10,'available','Cottage');
INSERT INTO "service" ("service_id","service_name","description","base_price","stock_total") VALUES (1,'Room Fee - Single (1 Pax)','Standard single room per night',1500.0,999),
 (2,'Room Fee - Double (2 Pax)','Standard double room per night',2500.0,999),
 (3,'Room Fee - Family (4 Pax)','Family room per night',4500.0,999),
 (4,'Room Fee - Suite (6 Pax)','Luxury suite per night',7000.0,999),
 (5,'Cottage Rental (10 Pax)','Large group cottage rental',10000.0,999),
 (6,'Meal: Solo (1 Pax)','Set meal for 1 person',350.0,999),
 (7,'Meal: Couple (2 Pax)','Set meal for 2 people',600.0,999),
 (8,'Meal: Family (4-6 Pax)','Bundle for 4-6 people',1500.0,999),
 (9,'Meal: Feast (6-10 Pax)','Bundle for 6-10 people',2800.0,999),
 (10,'Karaoke Rental','Per hour/session use',500.0,5),
 (11,'Pool Access','Pool day pass per pax',250.0,50),
 (12,'Spa Session','60-min spa per pax',800.0,5),
 (13,'Banana Boat','Per ride per group',1500.0,3),
 (14,'Jetski','Per 15-min ride',2000.0,3),
 (15,'Extra Bed','Folding bed with linens',500.0,10);
COMMIT;
