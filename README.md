# GrayEye IT Asset Management System

**Developer:** Aayaan Kamil  
**Project:** GrayEye IT Asset Management System  
**Repository:** [https://github.com/Aayaan721/GrayEye-IT-Asset-Management](https://github.com/Aayaan721/GrayEye-IT-Asset-Management)  

---

## 1. Project Overview

GrayEye IT Asset Management is a Flask web application built during an internship to track IT hardware records. It provides an inventory dashboard and lets users add, edit, search, filter, and delete assets, with CSV export for reporting. SQLite stores the records locally. The sample records are fictional and intended for demonstration.

This is an internship prototype, not a deployed company inventory service.

---

## 2. Objectives

- **Centralized Asset Tracking:** Maintain a single source of truth for all hardware equipment, serial numbers, models, and assigned custodians.
- **Lifecycle Status Management:** Accurately categorize hardware states into distinct operational categories (`Available`, `Assigned`, `Under Maintenance`, `Retired`).
- **Departmental Allocation & Cost Auditing:** Aggregate capital investment metrics and track departmental hardware distribution across Engineering, IT Operations, Product, Finance, and HR.
- **Rapid Search & Multi-Criteria Filtering:** Enable immediate discovery of hardware via multi-column full-text search, category filtering, and dynamic column sorting.
- **Data Integrity & Server-Side Validation:** Enforce strict validation rules (unique Asset IDs, regex sanitization, required fields, date formats) to prevent corrupted inventory data.
- **CSV Reporting:** Facilitate inventory review through one-click downloadable CSV inventory exports.

---

## 3. Technology Stack

The application is built using a clean **Model-View-Controller (MVC)** architectural design pattern without heavy or unnecessary external dependencies:

| Layer | Technology | Details |
| :--- | :--- | :--- |
| **Backend & Controller** | **Python 3.13 / Flask 3.1.3** | Lightweight WSGI web framework handling request routing, form sanitization, session flash messages, and response rendering. |
| **Model & Database** | **SQLite3** | Embedded relational database engine utilizing foreign key constraints, column indices (`idx_assets_status`, `idx_assets_category`, `idx_assets_department`, `idx_assets_asset_id`), and parameterized queries to prevent SQL injection. |
| **View & Templates** | **Jinja2 (HTML5 / Vanilla CSS3)** | Semantic HTML5 structure with custom-engineered CSS variables, responsive grid layouts, card components, and status badges. |
| **Client-Side Scripts** | **Vanilla JavaScript (ES6+)** | Pure lightweight JavaScript for modal dialog management, alert banner dismissal, and dynamic form input placeholder guidance without third-party libraries. |
| **Testing Suite** | **Python `unittest`** | Automated test suite comprising unit and integration tests verifying all application routes, CRUD flows, edge cases, and validations. |

---

## 4. Implemented Features

### 📊 Operations Dashboard
- **Key Performance Indicators:** Instant visualization of Total Tracked Assets, Available Units, Active Assignments, Units in Maintenance, Decommissioned/Retired Units, and Total Portfolio Valuation ($).
- **Recent Inventory Feed:** Chronological table displaying the latest hardware additions with direct links to asset inspection profiles.
- **Category & Departmental Distributions:** Breakdown of hardware allocation across corporate departments and equipment categories.

### 💻 Hardware Inventory Management
- **Multi-Field Search:** Real-time query filtering matching Asset ID, Device Name, Brand/Manufacturer, Serial Number, and Assigned Employee.
- **Categorical & Status Filters:** Instant filtering by lifecycle status (`Available`, `Assigned`, `Under Maintenance`, `Retired`), equipment category (`Laptops`, `Desktops`, `Monitors`, `Networking`, `Servers`, `Peripherals`, `Other`), and department.
- **Dynamic Multi-Column Sorting:** Sort table records by Asset ID, Device Name, Category, Brand, Serial Number, Assigned To, Department, Status, Purchase Date, Purchase Cost, or Creation Timestamp in ascending or descending order.

### 🛠️ Complete Asset CRUD Lifecycle
- **Create Asset:** Intuitive registration form featuring automatic suggestion for the next sequential Asset ID (`AST-xxxx`). Validates uniqueness, required attributes, non-negative procurement costs, and proper date formatting (`YYYY-MM-DD`).
- **Read / Detail Inspection:** Comprehensive asset view providing technical specifications, custodian details, department assignment, purchase date, cost, record timestamps, and operational notes.
- **Update Asset:** Safe edit workflow updating asset specifications, status transitions, and reassignments while locking the primary Asset ID to keep asset IDs consistent.
- **Delete Asset:** Dual-layer confirmation protection featuring an interactive modal overlay with fallback to a dedicated confirmation page (`/assets/<id>/delete`) to prevent accidental deletions.

### 📥 Audit & Reporting
- **On-Demand CSV Export:** Single-click export (`/export/csv`) generating a clean, timestamped CSV spreadsheet (`grayeye_assets_YYYYMMDD_HHMMSS.csv`) for inventory review.

### 🛡️ Defensive Engineering & Validation
- Parameterized SQL queries throughout to eliminate SQL injection vulnerabilities.
- Case-insensitive Asset ID uniqueness enforcement.
- Graceful error handling with custom 404 Not Found and 500 Internal Server Error pages.
- Flash notification alert system informing users of create, update, and delete actions.

---

## 5. Project Directory Structure

```
GrayEye-IT-Asset-Management/
├── static/
│   ├── css/
│   │   └── style.css            # Enterprise UI stylesheet (colors, typography, grid, modals)
│   └── js/
│       └── main.js              # Vanilla JS for modal dialogs and alert dismissals
├── templates/
│   ├── assets/
│   │   ├── confirm_delete.html  # Dedicated fallback asset deletion confirmation view
│   │   ├── detail.html          # Detailed single-asset profile and metadata inspection
│   │   ├── form.html            # Unified create and edit asset form
│   │   └── index.html           # Master asset inventory table with search, filters & sort
│   ├── 404.html                 # Custom 404 / resource not found template
│   ├── base.html                # Master layout template (navigation, flash messages, footer)
│   ├── dashboard.html           # Operations dashboard metrics and distribution views
│   └── index.html               # Welcome portal landing page
├── app.py                       # Main Flask application entry point, routes & business logic
├── database.py                  # Database connection factory, schema definition & seed data
├── test_app.py                  # Automated test suite (automated test cases)
├── requirements.txt             # Pinned project dependencies
├── .gitignore                   # Exclusions for virtual environments, caches, and local DBs
└── README.md                    # Project documentation, setup guide, and verification report
```

---

## 6. Installation & Setup Guide (Windows)

Follow these step-by-step instructions to set up and launch the application on a Windows machine.

### Prerequisites
- **Python 3.10+** (verified on Python 3.13)
- **Git**
- Windows PowerShell or Command Prompt

### Step 1: Clone the Repository
```powershell
git clone https://github.com/Aayaan721/GrayEye-IT-Asset-Management.git
cd GrayEye-IT-Asset-Management
```

### Step 2: Create a Python Virtual Environment
```powershell
python -m venv .venv
```

### Step 3: Activate the Virtual Environment
```powershell
# In PowerShell:
.\.venv\Scripts\Activate.ps1

# Or in Windows Command Prompt (cmd.exe):
.\.venv\Scripts\activate.bat
```

> *Note for PowerShell users:* If you encounter an execution policy error, enable local script execution for the current session by running:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
> ```

### Step 4: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 5: Database Initialization
The application automatically creates and initializes the SQLite database schema (`asset_management.db`) and seeds it with realistic default inventory assets upon first launch. 

To initialize or inspect the database explicitly before starting the server, run:
```powershell
python database.py
```
*Expected output:*
```
Database initialized successfully at: C:\Users\...\asset_management.db
```

### Step 6: Launch the Application

For any non-local use, provide a stable, randomly generated `SECRET_KEY` environment variable. The fallback key is intended only for local development.
```powershell
python app.py
```
*Expected output:*
```
 * Serving Flask app 'app'
 * Debug mode: off
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
```

### Step 7: Access the Application
Open any web browser and navigate to:
```
http://127.0.0.1:5000
```
or
```
http://localhost:5000
```

---

## 7. Automated Testing

The project includes a comprehensive automated test suite in `test_app.py` covering route availability, CRUD operations, database persistence, sorting algorithms, input validation, and CSV export.

### Running the Test Suite
Ensure your virtual environment is active, then execute:
```powershell
python -m unittest -v test_app.py
```

### Initial recorded test results
```
test_01_dashboard_route (test_app.TestAssetManagementSystem.test_01_dashboard_route)
Verify dashboard loads with 200 and displays summary data. ... ok
test_02_home_redirect (test_app.TestAssetManagementSystem.test_02_home_redirect)
Verify root route '/' redirects to '/dashboard'. ... ok
test_03_inventory_list (test_app.TestAssetManagementSystem.test_03_inventory_list)
Verify inventory list loads with all seeded assets. ... ok
test_04_inventory_search (test_app.TestAssetManagementSystem.test_04_inventory_search)
Verify search query filtering across name, serial, assignee. ... ok
test_05_inventory_filter_status (test_app.TestAssetManagementSystem.test_05_inventory_filter_status)
Verify filtering by status. ... ok
test_06_inventory_filter_category (test_app.TestAssetManagementSystem.test_06_inventory_filter_category)
Verify filtering by category. ... ok
test_07_asset_detail_existing (test_app.TestAssetManagementSystem.test_07_asset_detail_existing)
Verify viewing single asset details. ... ok
test_08_asset_detail_not_found (test_app.TestAssetManagementSystem.test_08_asset_detail_not_found)
Verify 404 response for non-existent asset. ... ok
test_09_add_asset_validation_failures (test_app.TestAssetManagementSystem.test_09_add_asset_validation_failures)
Verify server-side validation catches invalid inputs. ... ok
test_10_crud_lifecycle_create_read_update_delete (test_app.TestAssetManagementSystem.test_10_crud_lifecycle_create_read_update_delete)
Full end-to-end CRUD test of a new asset. ... ok
test_11_csv_export (test_app.TestAssetManagementSystem.test_11_csv_export)
Verify CSV export functionality. ... ok
test_12_persistence_after_db_reopen (test_app.TestAssetManagementSystem.test_12_persistence_after_db_reopen)
Verify that data written to SQLite persists across new connections. ... ok
test_13_advanced_sorting (test_app.TestAssetManagementSystem.test_13_advanced_sorting)
Verify sorting by serial_number, assigned_to, and purchase_cost. ... ok
test_14_regex_and_length_validation (test_app.TestAssetManagementSystem.test_14_regex_and_length_validation)
Verify regex and length boundaries on Asset ID and Name. ... ok
test_15_form_preserves_input_on_error (test_app.TestAssetManagementSystem.test_15_form_preserves_input_on_error)
Verify user form inputs are preserved when validation fails. ... ok
test_16_department_filter (test_app.TestAssetManagementSystem.test_16_department_filter)
Verify department filtering isolations. ... ok
test_17_dashboard_consistency_across_crud (test_app.TestAssetManagementSystem.test_17_dashboard_consistency_across_crud)
Verify dashboard statistics and inventory remain strictly consistent across CRUD operations. ... ok
test_18_invalid_category_and_status (test_app.TestAssetManagementSystem.test_18_invalid_category_and_status)
Verify invalid category and status values are rejected. ... ok
test_19_invalid_date_format (test_app.TestAssetManagementSystem.test_19_invalid_date_format)
Verify malformed purchase date formats are rejected. ... ok
test_20_search_empty_and_special_chars (test_app.TestAssetManagementSystem.test_20_search_empty_and_special_chars)
Verify search with non-matching strings and special characters handles gracefully. ... ok

----------------------------------------------------------------------
Ran 20 tests in 0.314s

OK
```

**Initial submission:** 20 tests passed before the security changes. The updated suite adds two CSRF tests. Run the command above to verify the current version; the original result does not establish a new test run.

---

## 8. Security Notes

The application uses parameterized SQL queries and validates input. Forms that create, edit, and delete records include a session-based CSRF token. The Flask session secret uses the `SECRET_KEY` environment variable, falling back to a randomly generated key for local development. Set a stable strong key for deployment; the local fallback changes on restart. Debug mode is off by default and can be enabled locally with `FLASK_DEBUG=1`.

This prototype has no authentication or role-based access control. Do not expose it to the public internet or use it for real confidential company records without additional protections and a security review. The SQLite file, local environment, and virtual environment are ignored by Git. The sample assets in `database.py` are fictional.

---

## 9. Conclusion

GrayEye IT Asset Management demonstrates common inventory tasks using Flask and SQLite. Future improvements could include authentication, a change-history log, and deployment configuration.
