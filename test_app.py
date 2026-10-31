"""Tests for asset routes, validation, CRUD, and SQLite persistence."""

import unittest
import sqlite3
import os
import tempfile
from app import app
import database

class TestAssetManagementSystem(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._original_db_path = database.DB_PATH
        cls._temp_dir = tempfile.TemporaryDirectory()
        database.DB_PATH = os.path.join(cls._temp_dir.name, "test_assets.db")
        database.init_db()

    @classmethod
    def tearDownClass(cls):
        database.DB_PATH = cls._original_db_path
        cls._temp_dir.cleanup()

    def setUp(self):
        app.config["TESTING"] = True
        app.config["CSRF_ENABLED"] = True
        self.client = app.test_client()

    def post_with_csrf(self, path, **kwargs):
        self.client.get("/dashboard")  # Initialize the session token.
        with self.client.session_transaction() as sess:
            token = sess["_csrf_token"]
        data = dict(kwargs.pop("data", {}) or {})
        data["_csrf_token"] = token
        return self.client.post(path, data=data, **kwargs)

    def test_01_dashboard_route(self):
        """Verify dashboard loads with 200 and displays summary data."""
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 200)
        content = response.data.decode("utf-8")
        self.assertIn("Operations Dashboard", content)
        self.assertIn("Total Assets", content)
        self.assertIn("Portfolio Value", content)
        self.assertIn("Recent Inventory Additions", content)
        self.assertIn("Category Breakdown", content)

    def test_02_home_redirect(self):
        """Verify root route '/' redirects to '/dashboard'."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/dashboard", response.headers["Location"])

    def test_03_inventory_list(self):
        """Verify inventory list loads with all seeded assets."""
        response = self.client.get("/assets")
        self.assertEqual(response.status_code, 200)
        content = response.data.decode("utf-8")
        self.assertIn("Hardware Inventory", content)
        self.assertIn("AST-1001", content)
        self.assertIn("MacBook Pro", content)

    def test_04_inventory_search(self):
        """Verify search query filtering across name, serial, assignee."""
        # Search by brand
        response = self.client.get("/assets?q=Apple")
        self.assertEqual(response.status_code, 200)
        content = response.data.decode("utf-8")
        self.assertIn("AST-1001", content)
        self.assertIn("MacBook Pro", content)
        self.assertNotIn("ThinkCentre", content)

        # Search by assignee
        response_assignee = self.client.get("/assets?q=Alex")
        content_assignee = response_assignee.data.decode("utf-8")
        self.assertIn("AST-1001", content_assignee)
        self.assertNotIn("ThinkCentre", content_assignee)

    def test_05_inventory_filter_status(self):
        """Verify filtering by status."""
        response = self.client.get("/assets?status=Available")
        self.assertEqual(response.status_code, 200)
        content = response.data.decode("utf-8")
        self.assertIn("AST-1003", content)
        # Should not show Assigned laptops
        self.assertNotIn("AST-1001", content)

    def test_06_inventory_filter_category(self):
        """Verify filtering by category."""
        response = self.client.get("/assets?category=Networking")
        self.assertEqual(response.status_code, 200)
        content = response.data.decode("utf-8")
        self.assertIn("Cisco Catalyst", content)
        self.assertNotIn("MacBook Pro", content)

    def test_07_asset_detail_existing(self):
        """Verify viewing single asset details."""
        response = self.client.get("/assets/AST-1001")
        self.assertEqual(response.status_code, 200)
        content = response.data.decode("utf-8")
        self.assertIn("MacBook Pro 16", content)
        self.assertIn("Alex Mercer", content)
        self.assertIn("Engineering", content)
        self.assertIn("C02G90XPMD6R", content)

    def test_08_asset_detail_not_found(self):
        """Verify 404 response for non-existent asset."""
        response = self.client.get("/assets/NON-EXISTENT-999")
        self.assertEqual(response.status_code, 404)
        content = response.data.decode("utf-8")
        self.assertIn("Resource Not Found", content)

    def test_09_add_asset_validation_failures(self):
        """Verify server-side validation catches invalid inputs."""
        # 1. Missing required name
        res1 = self.post_with_csrf("/assets/new", data={
            "asset_id": "TEST-001",
            "name": "",
            "category": "Laptops",
            "brand": "Dell",
            "status": "Available"
        }, follow_redirects=True)
        self.assertIn("Asset Name is required", res1.data.decode("utf-8"))

        # 2. Negative purchase cost
        res2 = self.post_with_csrf("/assets/new", data={
            "asset_id": "TEST-002",
            "name": "Test Laptop",
            "category": "Laptops",
            "brand": "Dell",
            "status": "Available",
            "purchase_cost": "-50.00"
        }, follow_redirects=True)
        self.assertIn("Purchase cost cannot be negative", res2.data.decode("utf-8"))

        # 3. Duplicate asset ID
        res3 = self.post_with_csrf("/assets/new", data={
            "asset_id": "AST-1001",  # Already exists
            "name": "Duplicate Asset",
            "category": "Laptops",
            "brand": "Dell",
            "status": "Available"
        }, follow_redirects=True)
        self.assertIn("already exists", res3.data.decode("utf-8"))

        # 4. Assigned status without employee
        res4 = self.post_with_csrf("/assets/new", data={
            "asset_id": "TEST-004",
            "name": "Assigned Laptop",
            "category": "Laptops",
            "brand": "Dell",
            "status": "Assigned",
            "assigned_to": ""  # empty
        }, follow_redirects=True)
        self.assertIn("Assigned Employee name is required", res4.data.decode("utf-8"))

    def test_10_crud_lifecycle_create_read_update_delete(self):
        """Full end-to-end CRUD test of a new asset."""
        test_id = "AST-9999"
        
        # 1. CREATE
        create_res = self.post_with_csrf("/assets/new", data={
            "asset_id": test_id,
            "name": "Autonomous Testing Drone",
            "category": "Other",
            "brand": "Grayeye Tech",
            "serial_number": "DRONE-SN-4040",
            "assigned_to": "Jordan Lee",
            "department": "Engineering",
            "purchase_date": "2024-05-01",
            "purchase_cost": "1899.99",
            "status": "Assigned",
            "notes": "Test flight inspection drone for facilities"
        }, follow_redirects=False)

        self.assertEqual(create_res.status_code, 302)
        self.assertIn(f"/assets/{test_id}", create_res.headers["Location"])

        # 2. READ (Detail)
        read_res = self.client.get(f"/assets/{test_id}")
        self.assertEqual(read_res.status_code, 200)
        detail_content = read_res.data.decode("utf-8")
        self.assertIn("Autonomous Testing Drone", detail_content)
        self.assertIn("Grayeye Tech", detail_content)
        self.assertIn("1,899.99", detail_content)
        self.assertIn("Jordan Lee", detail_content)

        # 3. UPDATE
        edit_res = self.post_with_csrf(f"/assets/{test_id}/edit", data={
            "name": "Autonomous Testing Drone v2 (Updated)",
            "category": "Other",
            "brand": "Grayeye Tech",
            "serial_number": "DRONE-SN-4040",
            "assigned_to": "",
            "department": "IT Operations",
            "purchase_date": "2024-05-01",
            "purchase_cost": "2100.00",
            "status": "Available",
            "notes": "Upgraded with thermal sensor."
        }, follow_redirects=True)

        self.assertEqual(edit_res.status_code, 200)
        updated_content = edit_res.data.decode("utf-8")
        self.assertIn("updated successfully", updated_content)
        self.assertIn("Autonomous Testing Drone v2 (Updated)", updated_content)
        self.assertIn("2,100.00", updated_content)

        # 4. DELETE CONFIRMATION PAGE (GET)
        confirm_res = self.client.get(f"/assets/{test_id}/delete")
        self.assertEqual(confirm_res.status_code, 200)
        self.assertIn("Confirm Permanent Asset Deletion", confirm_res.data.decode("utf-8"))

        # 5. DELETE EXECUTION (POST)
        delete_res = self.post_with_csrf(f"/assets/{test_id}/delete", follow_redirects=True)
        self.assertEqual(delete_res.status_code, 200)
        delete_content = delete_res.data.decode("utf-8")
        self.assertIn("was permanently deleted", delete_content)

        # Verify asset is no longer in DB
        verify_deleted = self.client.get(f"/assets/{test_id}")
        self.assertEqual(verify_deleted.status_code, 404)

    def test_11_csv_export(self):
        """Verify CSV export functionality."""
        response = self.client.get("/export/csv")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/csv")
        self.assertIn("attachment; filename=grayeye_assets_", response.headers.get("Content-Disposition", ""))
        content = response.data.decode("utf-8")
        self.assertIn("Asset ID,Asset Name,Category,Brand", content)
        self.assertIn("AST-1001", content)

    def test_12_persistence_after_db_reopen(self):
        """Verify that data written to SQLite persists across new connections."""
        test_id = "AST-7777"
        # Insert via client
        self.post_with_csrf("/assets/new", data={
            "asset_id": test_id,
            "name": "Persistence Verification Server",
            "category": "Servers",
            "brand": "Supermicro",
            "status": "Available",
            "purchase_cost": "4500.00"
        })

        # Directly query SQLite via a brand new independent connection
        conn = sqlite3.connect(database.DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM assets WHERE asset_id = ?", (test_id,))
        row = c.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["name"], "Persistence Verification Server")
        self.assertEqual(row["brand"], "Supermicro")
        self.assertEqual(row["purchase_cost"], 4500.00)

        # Clean up test row
        c.execute("DELETE FROM assets WHERE asset_id = ?", (test_id,))
        conn.commit()
        conn.close()

    def test_13_advanced_sorting(self):
        """Verify sorting by serial_number, assigned_to, and purchase_cost."""
        # Sort by serial number asc
        res_sn = self.client.get("/assets?sort=serial_number&order=asc")
        self.assertEqual(res_sn.status_code, 200)

        # Sort by assigned_to desc
        res_assign = self.client.get("/assets?sort=assigned_to&order=desc")
        self.assertEqual(res_assign.status_code, 200)

        # Sort by purchase_cost desc
        res_cost = self.client.get("/assets?sort=purchase_cost&order=desc")
        self.assertEqual(res_cost.status_code, 200)

    def test_14_regex_and_length_validation(self):
        """Verify regex and length boundaries on Asset ID and Name."""
        # Invalid characters in Asset ID
        res_invalid_id = self.post_with_csrf("/assets/new", data={
            "asset_id": "AST@INVALID#99",
            "name": "Invalid Tag Asset",
            "category": "Laptops",
            "brand": "Dell",
            "status": "Available"
        }, follow_redirects=True)
        self.assertIn("Asset ID may only contain letters", res_invalid_id.data.decode("utf-8"))

        # Excessively long name (> 150 chars)
        res_long_name = self.post_with_csrf("/assets/new", data={
            "asset_id": "AST-VALID-1",
            "name": "A" * 155,
            "category": "Laptops",
            "brand": "Dell",
            "status": "Available"
        }, follow_redirects=True)
        self.assertIn("Asset Name cannot exceed 150 characters", res_long_name.data.decode("utf-8"))

    def test_15_form_preserves_input_on_error(self):
        """Verify user form inputs are preserved when validation fails."""
        res = self.post_with_csrf("/assets/new", data={
            "asset_id": "AST-RETAIN-TEST",
            "name": "",  # Trigger validation error
            "brand": "Retained Brand Name",
            "category": "Servers",
            "status": "Available",
            "purchase_cost": "3200.50"
        }, follow_redirects=True)
        content = res.data.decode("utf-8")
        self.assertIn("Asset Name is required", content)
        self.assertIn("AST-RETAIN-TEST", content)
        self.assertIn("Retained Brand Name", content)
        self.assertIn("3200.50", content)

    def test_16_department_filter(self):
        """Verify department filtering isolations."""
        res_eng = self.client.get("/assets?department=Engineering")
        self.assertEqual(res_eng.status_code, 200)
        content_eng = res_eng.data.decode("utf-8")
        self.assertIn("AST-1001", content_eng)  # Alex Mercer in Engineering

        res_unassigned = self.client.get("/assets?department=Unassigned")
        self.assertEqual(res_unassigned.status_code, 200)

    def test_17_dashboard_consistency_across_crud(self):
        """Verify dashboard statistics and inventory remain strictly consistent across CRUD operations."""
        conn = database.get_db_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) AS total, COALESCE(SUM(purchase_cost), 0.0) AS val FROM assets")
        initial_row = c.fetchone()
        n_initial = initial_row["total"]
        v_initial = initial_row["val"]
        c.execute("SELECT COUNT(*) FROM assets WHERE status = 'Available'")
        avail_initial = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM assets WHERE status = 'Assigned'")
        assigned_initial = c.fetchone()[0]
        conn.close()

        test_tag = "AST-CONSIST-01"

        # 1. CREATE an Available asset with cost 1000.00
        self.post_with_csrf("/assets/new", data={
            "asset_id": test_tag,
            "name": "Consistency Testing Laptop",
            "category": "Laptops",
            "brand": "Lenovo",
            "status": "Available",
            "purchase_cost": "1000.00"
        }, follow_redirects=True)

        # Check DB & dashboard
        conn = database.get_db_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) AS total, COALESCE(SUM(purchase_cost), 0.0) AS val FROM assets")
        after_create = c.fetchone()
        self.assertEqual(after_create["total"], n_initial + 1)
        self.assertAlmostEqual(after_create["val"], v_initial + 1000.00, places=2)
        c.execute("SELECT COUNT(*) FROM assets WHERE status = 'Available'")
        self.assertEqual(c.fetchone()[0], avail_initial + 1)
        conn.close()

        # Check dashboard HTML reflects the new total
        res_dash = self.client.get("/dashboard")
        self.assertIn(str(n_initial + 1), res_dash.data.decode("utf-8"))

        # 2. UPDATE: Change to Assigned, cost 1500.00
        self.post_with_csrf(f"/assets/{test_tag}/edit", data={
            "name": "Consistency Testing Laptop (Updated)",
            "category": "Laptops",
            "brand": "Lenovo",
            "status": "Assigned",
            "assigned_to": "Jordan Lee",
            "department": "Engineering",
            "purchase_cost": "1500.00"
        }, follow_redirects=True)

        conn = database.get_db_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) AS total, COALESCE(SUM(purchase_cost), 0.0) AS val FROM assets")
        after_edit = c.fetchone()
        self.assertEqual(after_edit["total"], n_initial + 1)
        self.assertAlmostEqual(after_edit["val"], v_initial + 1500.00, places=2)
        c.execute("SELECT COUNT(*) FROM assets WHERE status = 'Available'")
        self.assertEqual(c.fetchone()[0], avail_initial)
        c.execute("SELECT COUNT(*) FROM assets WHERE status = 'Assigned'")
        self.assertEqual(c.fetchone()[0], assigned_initial + 1)
        conn.close()

        # 3. DELETE asset
        self.post_with_csrf(f"/assets/{test_tag}/delete", follow_redirects=True)

        conn = database.get_db_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) AS total, COALESCE(SUM(purchase_cost), 0.0) AS val FROM assets")
        after_del = c.fetchone()
        self.assertEqual(after_del["total"], n_initial)
        self.assertAlmostEqual(after_del["val"], v_initial, places=2)
        c.execute("SELECT COUNT(*) FROM assets WHERE status = 'Available'")
        self.assertEqual(c.fetchone()[0], avail_initial)
        c.execute("SELECT COUNT(*) FROM assets WHERE status = 'Assigned'")
        self.assertEqual(c.fetchone()[0], assigned_initial)
        conn.close()

    def test_18_invalid_category_and_status(self):
        """Verify invalid category and status values are rejected."""
        res_cat = self.post_with_csrf("/assets/new", data={
            "asset_id": "AST-BAD-CAT",
            "name": "Bad Category Asset",
            "category": "InvalidCategory123",
            "brand": "Dell",
            "status": "Available"
        }, follow_redirects=True)
        self.assertIn("Please select a valid category", res_cat.data.decode("utf-8"))

        res_st = self.post_with_csrf("/assets/new", data={
            "asset_id": "AST-BAD-ST",
            "name": "Bad Status Asset",
            "category": "Laptops",
            "brand": "Dell",
            "status": "NonExistentStatus"
        }, follow_redirects=True)
        self.assertIn("Please select a valid status", res_st.data.decode("utf-8"))

    def test_19_invalid_date_format(self):
        """Verify malformed purchase date formats are rejected."""
        res = self.post_with_csrf("/assets/new", data={
            "asset_id": "AST-BAD-DATE",
            "name": "Bad Date Asset",
            "category": "Laptops",
            "brand": "Dell",
            "status": "Available",
            "purchase_date": "15-01-2024"  # DD-MM-YYYY instead of YYYY-MM-DD
        }, follow_redirects=True)
        self.assertIn("Purchase date must be in YYYY-MM-DD format", res.data.decode("utf-8"))

    def test_21_csrf_rejects_missing_and_invalid_tokens(self):
        self.client.get("/assets/new")
        post_data = {"asset_id": "AST-CSRF-CHECK", "name": "CSRF check"}
        missing = self.client.post("/assets/new", data=post_data)
        self.assertEqual(missing.status_code, 400)
        invalid = self.client.post("/assets/new", data={**post_data, "_csrf_token": "invalid"})
        self.assertEqual(invalid.status_code, 400)

    def test_22_csrf_protects_delete_route(self):
        self.client.get("/dashboard")
        missing = self.client.post("/assets/AST-1001/delete")
        self.assertEqual(missing.status_code, 400)

    def test_20_search_empty_and_special_chars(self):
        """Verify search with non-matching strings and special characters handles gracefully."""
        res = self.client.get("/assets?q=XYZNonExistentKeyword999")
        self.assertEqual(res.status_code, 200)
        content = res.data.decode("utf-8")
        self.assertIn("No assets found", content)
        self.assertIn("Showing <strong>0</strong> assets", content)


if __name__ == "__main__":
    unittest.main()
