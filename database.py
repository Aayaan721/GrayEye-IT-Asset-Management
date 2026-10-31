"""
Database management module for Grayeye IT Asset Management System.
Handles SQLite connection, schema initialization, and initial seed data.
"""

import sqlite3
import os
from datetime import datetime

DATABASE_NAME = "asset_management.db"
# Place the database file in the project root directory
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), DATABASE_NAME)

# Standard predefined choices for consistent data entry
VALID_STATUSES = ["Available", "Assigned", "Under Maintenance", "Retired"]
VALID_CATEGORIES = [
    "Laptops",
    "Desktops",
    "Monitors",
    "Mobile Devices",
    "Networking",
    "Servers",
    "Peripherals",
    "Other"
]
VALID_DEPARTMENTS = [
    "Engineering",
    "IT Operations",
    "Product & Design",
    "Human Resources",
    "Finance",
    "Sales & Marketing",
    "Executive",
    "Customer Support",
    "Unassigned"
]


def get_db_connection():
    """
    Creates and returns a connection to the SQLite database.
    Configured with Row factory so columns can be accessed by name (dict-like).
    Foreign keys constraint enabled.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """
    Initializes the database schema if tables do not exist,
    and seeds sample data if the table is empty.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create assets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id TEXT UNIQUE NOT NULL COLLATE NOCASE,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            brand TEXT NOT NULL,
            serial_number TEXT,
            assigned_to TEXT,
            department TEXT,
            purchase_date TEXT,
            purchase_cost REAL DEFAULT 0.0,
            status TEXT NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Create indexes for fast lookup on frequent filter columns
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_status ON assets(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_category ON assets(category);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_department ON assets(department);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_asset_id ON assets(asset_id);")

    conn.commit()

    # Check if table is empty, if so, seed sample realistic data for Grayeye IT
    cursor.execute("SELECT COUNT(*) AS count FROM assets;")
    row = cursor.fetchone()
    if row["count"] == 0:
        seed_sample_data(conn)

    conn.close()


def seed_sample_data(conn):
    """
    Seeds initial realistic IT assets for Grayeye IT company.
    Provides immediate utility to test filtering, searching, and dashboard stats.
    """
    sample_assets = [
        (
            "AST-1001",
            "MacBook Pro 16\" M3 Max",
            "Laptops",
            "Apple",
            "C02G90XPMD6R",
            "Alex Mercer",
            "Engineering",
            "2024-01-15",
            3499.00,
            "Assigned",
            "Primary workstation for Senior Staff Architect. Equipped with 64GB RAM and 1TB SSD."
        ),
        (
            "AST-1002",
            "Dell XPS 15 9530",
            "Laptops",
            "Dell",
            "8HN2KL3",
            "Sarah Jenkins",
            "Product & Design",
            "2024-02-10",
            2199.50,
            "Assigned",
            "Assigned to UI/UX Lead. 3.5K OLED touchscreen display."
        ),
        (
            "AST-1003",
            "ThinkPad T14s Gen 4",
            "Laptops",
            "Lenovo",
            "PF-48X91A",
            None,
            "IT Operations",
            "2024-03-01",
            1450.00,
            "Available",
            "Ready in IT pool for new engineering onboarding."
        ),
        (
            "AST-1004",
            "Dell UltraSharp 27\" 4K (U2723QE)",
            "Monitors",
            "Dell",
            "CN-098K41-71618",
            "Alex Mercer",
            "Engineering",
            "2024-01-16",
            579.99,
            "Assigned",
            "USB-C Hub monitor with 90W power delivery on Desk 4B."
        ),
        (
            "AST-1005",
            "Dell UltraSharp 27\" 4K (U2723QE)",
            "Monitors",
            "Dell",
            "CN-098K41-71619",
            None,
            "IT Operations",
            "2024-01-16",
            579.99,
            "Available",
            "Spare unit stored in IT hardware cabinet 2."
        ),
        (
            "AST-1006",
            "Cisco Catalyst 9200 48-Port Switch",
            "Networking",
            "Cisco",
            "FOC2412L0AB",
            None,
            "IT Operations",
            "2023-11-05",
            3850.00,
            "Assigned",
            "Rack 1 Switch 2 in main server room MDF."
        ),
        (
            "AST-1007",
            "Dell PowerEdge R750 Server",
            "Servers",
            "Dell",
            "7G4M8K2",
            None,
            "IT Operations",
            "2023-08-20",
            8200.00,
            "Assigned",
            "Hosts internal virtualization clusters (Proxmox/ESXi)."
        ),
        (
            "AST-1008",
            "iPad Pro 12.9\" M2 Wi-Fi",
            "Mobile Devices",
            "Apple",
            "DMPXR208N9",
            "David Kim",
            "Sales & Marketing",
            "2024-04-12",
            1099.00,
            "Assigned",
            "Used for client demo presentations and mobile QA testing."
        ),
        (
            "AST-1009",
            "HP EliteBook 840 G8",
            "Laptops",
            "HP",
            "5CG1420XYZ",
            "Maria Rodriguez",
            "Finance",
            "2022-09-18",
            1280.00,
            "Under Maintenance",
            "Battery swelling detected; sent to authorized HP service center for replacement."
        ),
        (
            "AST-1010",
            "Logitech MX Master 3S Mouse",
            "Peripherals",
            "Logitech",
            "2315LZ09981",
            "Sarah Jenkins",
            "Product & Design",
            "2024-02-12",
            99.99,
            "Assigned",
            "Ergonomic wireless mouse paired with XPS 15."
        ),
        (
            "AST-1011",
            "Apple Studio Display 27\"",
            "Monitors",
            "Apple",
            "H6C9KL208N",
            None,
            "Engineering",
            "2023-05-14",
            1599.00,
            "Under Maintenance",
            "Thunderbolt cable connector loose; replacement cable requested."
        ),
        (
            "AST-1012",
            "Lenovo ThinkCentre M720q Tiny",
            "Desktops",
            "Lenovo",
            "MJ089912",
            None,
            "IT Operations",
            "2021-03-10",
            750.00,
            "Retired",
            "Decommissioned after office reception desk modernization. Hard drive wiped."
        ),
    ]

    cursor = conn.cursor()
    cursor.executemany("""
        INSERT INTO assets (
            asset_id, name, category, brand, serial_number,
            assigned_to, department, purchase_date, purchase_cost,
            status, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, sample_assets)
    conn.commit()


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DB_PATH)
