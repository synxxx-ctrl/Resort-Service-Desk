# 🏝️ Resort Service Desk System

A **Python-based desktop application** for managing resort operations
such as reservations, check-ins, billing, maintenance tracking, and
financial reporting.\
Built with **customtkinter** for a modern GUI and **SQLite3** for
lightweight, reliable data storage.

## 🚀 Features

### 🛠️ Admin Dashboard

Central hub to access all system functionalities.

### 🏨 Reservation Management

-   Create bookings for **overnight stays** or **day tours**.
-   View and manage upcoming, ongoing, and completed reservations.

### 🧳 Check-in / Check-out

-   Track guest stays.
-   Automatic bill calculations on checkout.

### 💳 Billing & Payments

-   Compute fees dynamically.
-   Process payments and store transaction history.

### 🧹 Maintenance Tracking

-   Report broken amenities.
-   Handle item swaps and apply refunds when necessary.

### 👤 Customer Management

-   Register new guests.
-   View complete customer history and past reservations.

### 📊 Reports

Generate: - Daily reports - Weekly reports - Monthly reports - Custom
date range financial summaries

## 🛠️ Tech Stack

-   **Language:** Python 3.x
-   **GUI Framework:** customtkinter (modern Tkinter wrapper)
-   **Database:** SQLite3
-   **Libraries:**
    -   tkcalendar -- date selection components
    -   tkinter -- standard GUI library

## 📥 Setup & Installation

### 1. Clone the Repository

    git clone https://github.com/synxx-ctrl/resort-service-desk.git
    cd resort-service-desk

### 2. Install Dependencies

Make sure Python 3.x is installed.

    pip install customtkinter tkcalendar

### 3. Initialize the Database

⚠️ Important: If an existing resort.db is present, delete it to avoid
schema conflicts.

Run the initialization script:

    python init_db.py

This will generate a new resort.db with all required tables and a
default admin account.

### 4. Run the Application

    python MainApp.py

## 🔑 Default Credentials

-   Username: admin
-   Password: admin

## 📂 Project Structure

    resort-service-desk/
    │
    ├── MainApp.py               # Entry point of the application
    ├── admin_dashboard.py       # Admin main menu UI
    │
    ├── controllers/             # Core logic (reservations, payments, maintenance)
    │
    ├── models.py                # Database queries and data handling
    ├── db.py                    # Database connection helper
    ├── init_db.py               # Database creation & setup script
    │
    └── README.md                # Project documentation

## 📝 Notes

-   This project is currently a work in progress for a college
    requirement.
-   Ensure tkcalendar is installed; otherwise, the date fields will use
    a text entry fallback.
-   Built and maintained by: **ALCARAZ, Tristan** & **MERCADO, Marc
    Ivan** -- BSIT 2106
