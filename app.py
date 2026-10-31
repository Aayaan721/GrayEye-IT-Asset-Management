"""
Grayeye IT Asset Management System
Main Flask Application

Architecture Note (for CSE students):
This application follows the MVC (Model-View-Controller) design pattern:
- Model: SQLite database managed via database.py with parameterized queries.
- View: Jinja2 templates (HTML + CSS + vanilla JS) in the /templates and /static directories.
- Controller: Flask route handlers defined in this file which parse HTTP requests,
  validate input, interact with the model, and render views or redirect.
"""

import os
import csv
import io
import re
import sqlite3
from datetime import datetime
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort,
    Response
)

import database
from database import (
    get_db_connection,
    init_db,
    VALID_STATUSES,
    VALID_CATEGORIES,
    VALID_DEPARTMENTS
)

app = Flask(__name__)
# Secure secret key for session management and flash messages
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "grayeye-it-asset-mgmt-secret-key-2026")


@app.context_processor
def inject_global_data():
    """
    Context processor injects commonly needed lists into every Jinja template,
    avoiding repetitive passing in route return calls.
    """
    return {
        "valid_statuses": VALID_STATUSES,
        "valid_categories": VALID_CATEGORIES,
        "valid_departments": VALID_DEPARTMENTS,
        "current_year": datetime.now().year,
        "app_name": "Grayeye IT Asset Management"
    }


def get_next_asset_id():
    """
    Calculates the next recommended asset ID based on existing AST-xxxx IDs.
    Helps users avoid guessing when creating new assets.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT asset_id FROM assets WHERE asset_id LIKE 'AST-%';")
    rows = cursor.fetchall()
    conn.close()

    max_num = 1000
    for row in rows:
        val = row["asset_id"].replace("AST-", "").strip()
        if val.isdigit():
            num = int(val)
            if num > max_num:
                max_num = num

    return f"AST-{max_num + 1}"


# ==========================================
# ROUTES: Dashboard & Overview
# ==========================================

@app.route("/")
def home():
    """Redirect root path to the primary dashboard."""
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():
    """
    Dashboard summary page.
    Aggregates asset counts, status breakdown, category distribution,
    financial investment metrics, and recent inventory items.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Total count and total purchase cost
    cursor.execute("""
        SELECT 
            COUNT(*) AS total_assets,
            COALESCE(SUM(purchase_cost), 0.0) AS total_value
        FROM assets;
    """)
    totals = cursor.fetchone()
    total_assets = totals["total_assets"]
    total_value = totals["total_value"]

    # 2. Count by Status
    cursor.execute("""
        SELECT status, COUNT(*) AS count
        FROM assets
        GROUP BY status;
    """)
    status_rows = cursor.fetchall()
    # Initialize dictionary with zeros for all valid statuses
    status_counts = {st: 0 for st in VALID_STATUSES}
    for row in status_rows:
        if row["status"] in status_counts:
            status_counts[row["status"]] = row["count"]

    # 3. Count by Category
    cursor.execute("""
        SELECT category, COUNT(*) AS count
        FROM assets
        GROUP BY category
        ORDER BY count DESC, category ASC;
    """)
    category_counts = cursor.fetchall()

    # 4. Count by Department
    cursor.execute("""
        SELECT COALESCE(NULLIF(department, ''), 'Unassigned') AS dept_name, COUNT(*) AS count
        FROM assets
        GROUP BY dept_name
        ORDER BY count DESC;
    """)
    department_counts = cursor.fetchall()

    # 5. Recently added or modified assets (latest 6)
    cursor.execute("""
        SELECT asset_id, name, category, brand, assigned_to, department, status, purchase_cost, created_at
        FROM assets
        ORDER BY id DESC
        LIMIT 6;
    """)
    recent_assets = cursor.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        total_assets=total_assets,
        total_value=total_value,
        status_counts=status_counts,
        category_counts=category_counts,
        department_counts=department_counts,
        recent_assets=recent_assets
    )


# ==========================================
# ROUTES: Asset Inventory & Search
# ==========================================

@app.route("/assets")
def asset_list():
    """
    Asset Inventory Table with dynamic multi-field search and filtering.
    Supports:
    - Search query string ('q'): checks asset_id, name, brand, serial_number, assigned_to
    - Filter by status
    - Filter by category
    - Filter by department
    - Dynamic sorting by chosen column and order
    """
    search_query = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "").strip()
    category_filter = request.args.get("category", "").strip()
    department_filter = request.args.get("department", "").strip()
    sort_by = request.args.get("sort", "created_at").strip()
    sort_order = request.args.get("order", "desc").strip().lower()

    # Whitelist allowed sorting columns to prevent SQL injection
    valid_sort_columns = {
        "asset_id": "asset_id",
        "name": "name",
        "category": "category",
        "brand": "brand",
        "serial_number": "serial_number",
        "assigned_to": "assigned_to",
        "department": "department",
        "status": "status",
        "purchase_cost": "purchase_cost",
        "purchase_date": "purchase_date",
        "created_at": "id"
    }
    sql_sort_column = valid_sort_columns.get(sort_by, "id")
    sql_sort_direction = "DESC" if sort_order == "desc" else "ASC"

    # Build parameterized query safely
    sql_conditions = []
    params = []

    if search_query:
        # Match case-insensitively across multiple fields
        sql_conditions.append("""
            (asset_id LIKE ? OR name LIKE ? OR brand LIKE ? OR serial_number LIKE ? OR assigned_to LIKE ?)
        """)
        wildcard = f"%{search_query}%"
        params.extend([wildcard, wildcard, wildcard, wildcard, wildcard])

    if status_filter:
        sql_conditions.append("status = ?")
        params.append(status_filter)

    if category_filter:
        sql_conditions.append("category = ?")
        params.append(category_filter)

    if department_filter:
        if department_filter == "Unassigned":
            sql_conditions.append("(department IS NULL OR department = '' OR department = 'Unassigned')")
        else:
            sql_conditions.append("department = ?")
            params.append(department_filter)

    where_clause = ""
    if sql_conditions:
        where_clause = "WHERE " + " AND ".join(sql_conditions)

    query = f"""
        SELECT id, asset_id, name, category, brand, serial_number,
               assigned_to, department, purchase_date, purchase_cost,
               status, notes, created_at, updated_at
        FROM assets
        {where_clause}
        ORDER BY {sql_sort_column} {sql_sort_direction};
    """

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    assets = cursor.fetchall()
    conn.close()

    filters_applied = bool(search_query or status_filter or category_filter or department_filter)

    return render_template(
        "assets/index.html",
        assets=assets,
        search_query=search_query,
        selected_status=status_filter,
        selected_category=category_filter,
        selected_department=department_filter,
        sort_by=sort_by,
        sort_order=sort_order,
        total_results=len(assets),
        filters_applied=filters_applied
    )


# ==========================================
# ROUTES: Add Asset
# ==========================================

@app.route("/assets/new", methods=["GET", "POST"])
def asset_create():
    """
    Renders the asset creation form (GET) and processes form submission (POST).
    Performs comprehensive server-side validation.
    """
    if request.method == "POST":
        # Extract and sanitize form values
        asset_id = request.form.get("asset_id", "").strip().upper()
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        brand = request.form.get("brand", "").strip()
        serial_number = request.form.get("serial_number", "").strip()
        assigned_to = request.form.get("assigned_to", "").strip()
        department = request.form.get("department", "").strip()
        purchase_date = request.form.get("purchase_date", "").strip()
        purchase_cost_raw = request.form.get("purchase_cost", "").strip()
        status = request.form.get("status", "").strip()
        notes = request.form.get("notes", "").strip()

        # Validation errors collector
        errors = []

        if not asset_id:
            errors.append("Asset ID is required (e.g. AST-1013).")
        elif len(asset_id) > 50:
            errors.append("Asset ID cannot exceed 50 characters.")
        elif not re.match(r"^[A-Za-z0-9\-_]+$", asset_id):
            errors.append("Asset ID may only contain letters, numbers, hyphens, and underscores.")

        if not name:
            errors.append("Asset Name is required.")
        elif len(name) > 150:
            errors.append("Asset Name cannot exceed 150 characters.")

        if not category or category not in VALID_CATEGORIES:
            errors.append(f"Please select a valid category from: {', '.join(VALID_CATEGORIES)}.")

        if not brand:
            errors.append("Brand / Manufacturer is required.")

        if not status or status not in VALID_STATUSES:
            errors.append(f"Please select a valid status from: {', '.join(VALID_STATUSES)}.")

        # If status is Assigned, employee is recommended/required
        if status == "Assigned" and not assigned_to:
            errors.append("When status is 'Assigned', an Assigned Employee name is required.")

        # Purchase cost numeric check
        purchase_cost = 0.0
        if purchase_cost_raw:
            try:
                purchase_cost = float(purchase_cost_raw)
                if purchase_cost < 0:
                    errors.append("Purchase cost cannot be negative.")
            except ValueError:
                errors.append("Purchase cost must be a valid number.")

        # Purchase date format check (if provided)
        if purchase_date:
            try:
                datetime.strptime(purchase_date, "%Y-%m-%d")
            except ValueError:
                errors.append("Purchase date must be in YYYY-MM-DD format.")

        # Check for duplicate Asset ID in the database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM assets WHERE asset_id = ? COLLATE NOCASE;", (asset_id,))
        if cursor.fetchone() is not None:
            errors.append(f"An asset with ID '{asset_id}' already exists. Please choose a unique ID.")

        if errors:
            conn.close()
            for err in errors:
                flash(err, "danger")
            # Preserve user input on validation error
            form_data = request.form.to_dict()
            return render_template("assets/form.html", form_action="create", asset=form_data)

        # Insert new record using parameterized query
        try:
            cursor.execute("""
                INSERT INTO assets (
                    asset_id, name, category, brand, serial_number,
                    assigned_to, department, purchase_date, purchase_cost,
                    status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                asset_id,
                name,
                category,
                brand,
                serial_number or None,
                assigned_to or None,
                department or None,
                purchase_date or None,
                purchase_cost,
                status,
                notes or None
            ))
            conn.commit()
            conn.close()

            flash(f"Asset '{name}' ({asset_id}) was added successfully!", "success")
            return redirect(url_for("asset_detail", asset_id=asset_id))

        except sqlite3.IntegrityError as e:
            conn.close()
            flash(f"Database error: {str(e)}", "danger")
            return render_template("assets/form.html", form_action="create", asset=request.form.to_dict())

    # GET request: render empty form with suggested next ID
    suggested_id = get_next_asset_id()
    default_asset = {
        "asset_id": suggested_id,
        "status": "Available",
        "purchase_cost": "0.00"
    }
    return render_template("assets/form.html", form_action="create", asset=default_asset)


# ==========================================
# ROUTES: Asset Detail
# ==========================================

@app.route("/assets/<asset_id>")
def asset_detail(asset_id):
    """
    Displays full details for a single asset.
    Handles non-existent asset gracefully with a 404 alert.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM assets WHERE asset_id = ? COLLATE NOCASE;
    """, (asset_id.strip(),))
    asset = cursor.fetchone()
    conn.close()

    if asset is None:
        flash(f"Asset with ID '{asset_id}' was not found.", "warning")
        return render_template("404.html", message=f"Asset '{asset_id}' does not exist in inventory."), 404

    return render_template("assets/detail.html", asset=asset)


# ==========================================
# ROUTES: Edit Asset
# ==========================================

@app.route("/assets/<asset_id>/edit", methods=["GET", "POST"])
def asset_edit(asset_id):
    """
    Renders edit form (GET) and processes updates (POST).
    Asset ID remains read-only to preserve identity integrity across audit records.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM assets WHERE asset_id = ? COLLATE NOCASE;", (asset_id.strip(),))
    existing_asset = cursor.fetchone()

    if existing_asset is None:
        conn.close()
        flash(f"Asset '{asset_id}' not found for editing.", "danger")
        return redirect(url_for("asset_list"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        brand = request.form.get("brand", "").strip()
        serial_number = request.form.get("serial_number", "").strip()
        assigned_to = request.form.get("assigned_to", "").strip()
        department = request.form.get("department", "").strip()
        purchase_date = request.form.get("purchase_date", "").strip()
        purchase_cost_raw = request.form.get("purchase_cost", "").strip()
        status = request.form.get("status", "").strip()
        notes = request.form.get("notes", "").strip()

        errors = []

        if not name:
            errors.append("Asset Name is required.")
        elif len(name) > 150:
            errors.append("Asset Name cannot exceed 150 characters.")

        if not category or category not in VALID_CATEGORIES:
            errors.append(f"Please select a valid category from: {', '.join(VALID_CATEGORIES)}.")

        if not brand:
            errors.append("Brand / Manufacturer is required.")

        if not status or status not in VALID_STATUSES:
            errors.append(f"Please select a valid status from: {', '.join(VALID_STATUSES)}.")

        if status == "Assigned" and not assigned_to:
            errors.append("When status is 'Assigned', an Assigned Employee name is required.")

        purchase_cost = 0.0
        if purchase_cost_raw:
            try:
                purchase_cost = float(purchase_cost_raw)
                if purchase_cost < 0:
                    errors.append("Purchase cost cannot be negative.")
            except ValueError:
                errors.append("Purchase cost must be a valid number.")

        if purchase_date:
            try:
                datetime.strptime(purchase_date, "%Y-%m-%d")
            except ValueError:
                errors.append("Purchase date must be in YYYY-MM-DD format.")

        if errors:
            conn.close()
            for err in errors:
                flash(err, "danger")
            # Preserve user modifications while keeping existing ID
            merged_asset = dict(existing_asset)
            merged_asset.update(request.form.to_dict())
            return render_template("assets/form.html", form_action="edit", asset=merged_asset)

        # Update database with parameterized query
        cursor.execute("""
            UPDATE assets
            SET name = ?,
                category = ?,
                brand = ?,
                serial_number = ?,
                assigned_to = ?,
                department = ?,
                purchase_date = ?,
                purchase_cost = ?,
                status = ?,
                notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE asset_id = ? COLLATE NOCASE;
        """, (
            name,
            category,
            brand,
            serial_number or None,
            assigned_to or None,
            department or None,
            purchase_date or None,
            purchase_cost,
            status,
            notes or None,
            asset_id
        ))
        conn.commit()
        conn.close()

        flash(f"Asset '{asset_id}' was updated successfully!", "success")
        return redirect(url_for("asset_detail", asset_id=asset_id))

    conn.close()
    return render_template("assets/form.html", form_action="edit", asset=existing_asset)


# ==========================================
# ROUTES: Delete Asset (Safe Destructive Action)
# ==========================================

@app.route("/assets/<asset_id>/delete", methods=["GET", "POST"])
def asset_delete(asset_id):
    """
    Deletes an asset with confirmation.
    - POST: Executes deletion and redirects to inventory with flash.
    - GET: Renders a dedicated confirmation warning page (fallback for browsers/no-js).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM assets WHERE asset_id = ? COLLATE NOCASE;", (asset_id.strip(),))
    asset = cursor.fetchone()

    if asset is None:
        conn.close()
        flash(f"Asset '{asset_id}' not found.", "warning")
        return redirect(url_for("asset_list"))

    if request.method == "POST":
        cursor.execute("DELETE FROM assets WHERE asset_id = ? COLLATE NOCASE;", (asset_id.strip(),))
        conn.commit()
        conn.close()

        flash(f"Asset '{asset['name']}' ({asset_id}) was permanently deleted.", "info")
        return redirect(url_for("asset_list"))

    # GET request shows safe confirmation page
    conn.close()
    return render_template("assets/confirm_delete.html", asset=asset)


# ==========================================
# ROUTES: Data Export (CSV)
# ==========================================

@app.route("/export/csv")
def export_csv():
    """
    Exports current asset inventory as a downloadable CSV spreadsheet.
    Useful utility for IT audits and executive reporting.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT asset_id, name, category, brand, serial_number,
               assigned_to, department, purchase_date, purchase_cost,
               status, notes, created_at, updated_at
        FROM assets
        ORDER BY id ASC;
    """)
    rows = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Asset ID", "Asset Name", "Category", "Brand", "Serial Number",
        "Assigned To", "Department", "Purchase Date", "Purchase Cost ($)",
        "Status", "Notes", "Created At", "Updated At"
    ])

    for r in rows:
        writer.writerow([
            r["asset_id"],
            r["name"],
            r["category"],
            r["brand"],
            r["serial_number"] or "",
            r["assigned_to"] or "",
            r["department"] or "",
            r["purchase_date"] or "",
            f"{r['purchase_cost']:.2f}" if r["purchase_cost"] is not None else "0.00",
            r["status"],
            r["notes"] or "",
            r["created_at"],
            r["updated_at"]
        ])

    csv_data = output.getvalue()
    filename = f"grayeye_assets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )


# ==========================================
# ERROR HANDLERS
# ==========================================

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html", message="The requested page or asset could not be found."), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template("404.html", message="An internal server error occurred. Please contact IT support."), 500


# Application Startup Initialization
with app.app_context():
    init_db()


if __name__ == "__main__":
    # Ensure database tables exist before serving traffic
    init_db()
    app.run(debug=True)
