Resort Service Desk System 

A Python-based desktop application for managing resort operations, including reservations, check-ins, billing, maintenance tracking, and reports. This project was built using customtkinter for the GUI and sqlite3 for data management.

Features:

Admin Dashboard: Central hub for managing all resort activities.

Reservation Management: Create bookings for overnight stays or day tours.

Check-in / Check-out: Manage guest stays and calculate bills automatically.

Billing & Payments: Process payments and view transaction history.

Maintenance Tracking: Report broken amenities, handle swaps, and process refunds.

Customer Management: Register new guests and view customer history.

Reports: Generate daily, weekly, monthly, or custom date range financial reports.

Tech Stack:

Language: Python 3.x

GUI: customtkinter (Modern Tkinter wrapper)

Database: SQLite 3

Libraries: tkcalendar (for date picking), tkinter (standard library)

Setup & Installation:

Clone the repository (or download the files):

git clone [https://github.com/your-username/resort-service-desk.git](https://github.com/your-username/resort-service-desk.git)
cd resort-service-desk


Install dependencies:
Make sure you have Python installed. Then run:

pip install customtkinter tkcalendar


Initialize the Database:

Important: If you have an existing resort.db, delete it first to ensure the schema is updated.

Run the initialization script:

python init_db.py


This will create a fresh resort.db file with the necessary tables and default admin account.

Run the Application:

python MainApp.py


Default Credentials:

Username: admin

Password: admin

Project Structure 📂

MainApp.py: Entry point of the application.

admin_dashboard.py: Main menu UI for administrators.

controllers/: Contains logic for reservations, payments, maintenance, etc.

models.py: Database queries and data handling logic.

db.py: Database connection handler.

init_db.py: Script to set up the database schema.

Notes 📝

This project is a work in progress for a college requirement.

Ensure tkcalendar is installed for the date picker to work correctly; otherwise, it falls back to a text entry field.

Created by ALCARAZ, Tristan and MERCADO, Marc Ivan - BSIT 2106