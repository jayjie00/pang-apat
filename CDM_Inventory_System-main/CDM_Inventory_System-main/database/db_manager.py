import sqlite3
import os
import json
import csv # Required for downloading reports
import datetime

# Ensure we use the correct absolute path for the database file
DB_PATH = os.path.join(os.path.dirname(__file__), "inventory_system.db")


def _ensure_admin_users_columns(cursor):
    cursor.execute("PRAGMA table_info(admin_users)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'email' not in columns:
        cursor.execute("ALTER TABLE admin_users ADD COLUMN email TEXT")
    if 'reset_code' not in columns:
        cursor.execute("ALTER TABLE admin_users ADD COLUMN reset_code TEXT")
    if 'reset_code_expiry' not in columns:
        cursor.execute("ALTER TABLE admin_users ADD COLUMN reset_code_expiry TIMESTAMP")
    if 'reset_code_sent_at' not in columns:
        cursor.execute("ALTER TABLE admin_users ADD COLUMN reset_code_sent_at TIMESTAMP")


def initialize_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Staff/Admin Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS admin_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        username TEXT UNIQUE, 
        password TEXT, 
        role TEXT,
        security_answer TEXT,
        email TEXT,
        reset_code TEXT,
        reset_code_expiry TIMESTAMP,
        reset_code_sent_at TIMESTAMP)''')
    _ensure_admin_users_columns(cursor)
    
    # 2. Inventory Table - property_id tracks the specific sticker on the equipment
    cursor.execute('''CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        item_name TEXT, 
        brand TEXT, 
        quantity INTEGER, 
        status TEXT, 
        category TEXT, 
        image_path TEXT,
        property_id TEXT DEFAULT 'N/A')''')

    # 3. Requests Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        student_name TEXT, 
        items_json TEXT, 
        purpose TEXT, 
        status TEXT DEFAULT 'PENDING', 
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # Create Initial Admin if none exists
    cursor.execute("SELECT COUNT(*) FROM admin_users WHERE username = 'admin'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""INSERT INTO admin_users (username, password, role, security_answer, email) 
                          VALUES ('admin', 'cdm123', 'Admin', 'recovery', 'admin@cdm.local')""")
    else:
        cursor.execute("UPDATE admin_users SET email='admin@cdm.local' WHERE username='admin' AND (email IS NULL OR email='')")

    conn.commit()
    conn.close()

def verify_admin(username, password):
    """Checks credentials and returns (Success, Role) for the login signal."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM admin_users WHERE username=? AND password=?", (username, password))
        result = cursor.fetchone()
        conn.close()
        # Returns tuple (True, 'Admin') or (True, 'Staff') if found, else (False, None)
        return (True, result[0]) if result else (False, None)
    except Exception as e:
        print(f"Login Error: {e}")
        return False, None

# --- PASSWORD RECOVERY LOGIC ---

def verify_security_answer(username, answer):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT id FROM admin_users WHERE username=? AND security_answer=?", (username, answer))
    res = cursor.fetchone(); conn.close()
    return res is not None

def get_user_by_email(email):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM admin_users WHERE email = ?", (email,))
    user = cursor.fetchone(); conn.close()
    return user

def store_reset_code(email, code, expiry, sent_at):
    try:
        conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
        cursor.execute("UPDATE admin_users SET reset_code=?, reset_code_expiry=?, reset_code_sent_at=? WHERE email=?", 
                       (code, expiry, sent_at, email))
        conn.commit(); conn.close(); return True
    except Exception as e:
        print(f"Store reset code error: {e}")
        return False

def get_reset_code_info(email):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT reset_code, reset_code_expiry, reset_code_sent_at FROM admin_users WHERE email=?", (email,))
    row = cursor.fetchone(); conn.close()
    return row

def verify_reset_code(email, code):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT reset_code, reset_code_expiry FROM admin_users WHERE email=?", (email,))
    row = cursor.fetchone(); conn.close()
    if not row:
        return False
    stored_code, expiry = row
    if stored_code != code or not expiry:
        return False
    try:
        expiry_dt = datetime.datetime.fromisoformat(expiry)
    except Exception:
        return False
    return expiry_dt >= datetime.datetime.utcnow()

def reset_password_by_email(email, new_password):
    try:
        conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
        cursor.execute("UPDATE admin_users SET password=?, reset_code=NULL, reset_code_expiry=NULL, reset_code_sent_at=NULL WHERE email=?", 
                       (new_password, email))
        conn.commit(); conn.close(); return True
    except Exception as e:
        print(f"Reset password by email error: {e}")
        return False

def reset_password(username, new_password):
    try:
        conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
        cursor.execute("UPDATE admin_users SET password=? WHERE username=?", (new_password, username))
        conn.commit(); conn.close(); return True
    except Exception as e:
        print(f"Reset password error: {e}")
        return False

# --- DOWNLOAD / EXPORT LOGIC ---

def export_to_csv(data, filename, headers):
    try:
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            writer.writerows(data)
        return True
    except Exception as e:
        print(f"Export Error: {e}")
        return False

# --- USER MANAGEMENT ---

def add_user(u, p, r, email=""):
    """Adds a user and assigns them a role (Admin or Staff)."""
    try:
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("INSERT INTO admin_users (username, password, role, security_answer, email) VALUES (?,?,?,?,?)", 
                  (u, p, r, 'recovery', email))
        conn.commit(); conn.close(); return True
    except Exception as e:
        print(f"Add user error: {e}")
        return False

def update_admin_credentials(new_username, new_password):
    try:
        conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
        cursor.execute("UPDATE admin_users SET username = ?, password = ? WHERE id = 1", 
                       (new_username, new_password))
        conn.commit(); conn.close(); return True
    except Exception as e:
        print(f"Error updating admin: {e}")
        return False

def get_all_users():
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT id, username, role FROM admin_users")
    users = cursor.fetchall(); conn.close()
    return users

def get_user_by_id(user_id):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT id, username, password, role, email FROM admin_users WHERE id=?", (user_id,))
    user = cursor.fetchone(); conn.close()
    return user

def update_staff_credentials(user_id, username, password, email):
    try:
        conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
        cursor.execute("UPDATE admin_users SET username=?, password=?, email=? WHERE id=?", 
                       (username, password, email, user_id))
        conn.commit(); conn.close(); return True
    except Exception as e:
        print(f"Error updating staff credentials: {e}")
        return False

def delete_user(user_id):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("DELETE FROM admin_users WHERE id = ?", (user_id,))
    conn.commit(); conn.close()

# --- INVENTORY LOGIC ---

def get_all_items():
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT * FROM inventory"); items = c.fetchall(); conn.close()
    return items

def add_inventory_item(name, brand, qty, cat, img="", prop_id="N/A"):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("""INSERT INTO inventory (item_name, brand, quantity, status, category, image_path, property_id) 
                 VALUES (?,?,?,?,?,?,?)""", (name, brand, qty, 'Available', cat, img, prop_id))
    conn.commit(); conn.close()

def update_inventory_item(item_id, name, brand, qty, cat, img, prop_id="N/A"):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("""UPDATE inventory SET item_name=?, brand=?, quantity=?, category=?, image_path=?, property_id=? 
                 WHERE id=?""", (name, brand, qty, cat, img, prop_id, item_id))
    conn.commit(); conn.close()

def delete_inventory_item(item_id):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("DELETE FROM inventory WHERE id = ?", (item_id,))
    conn.commit(); conn.close()

def deduct_stock(item_name, quantity, prop_id="N/A"):
    """Deducts stock. If Equipment/Sound, marks specific Property ID as Borrowed."""
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    if prop_id != "N/A":
        cursor.execute("""UPDATE inventory SET quantity = 0, status = 'Borrowed' 
                          WHERE item_name = ? AND property_id = ?""", (item_name, prop_id))
    else:
        cursor.execute("UPDATE inventory SET quantity = quantity - ? WHERE item_name = ?", (quantity, item_name))
    conn.commit(); conn.close()

def return_item(item_name, quantity, prop_id="N/A"):
    """Restores stock. If Equipment/Sound, marks specific Property ID as Available."""
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    if prop_id != "N/A":
        cursor.execute("""UPDATE inventory SET quantity = 1, status = 'Available' 
                          WHERE item_name = ? AND property_id = ?""", (item_name, prop_id))
    else:
        cursor.execute("UPDATE inventory SET quantity = quantity + ? WHERE item_name = ?", (quantity, item_name))
    conn.commit(); conn.close()

# --- KIOSK GROUPING LOGIC ---

def get_grouped_items():
    """Returns unique item types with their total available quantity for the Kiosk grid."""
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    # Groups by Name and Brand so identical assets appear as one card
    cursor.execute("""
        SELECT MIN(id), item_name, brand, SUM(quantity), status, category, image_path 
        FROM inventory 
        WHERE quantity > 0 
        GROUP BY item_name, brand
    """)
    items = cursor.fetchall(); conn.close()
    return items

def get_available_asset_id(name, brand):
    """Finds the first available individual unit's Property ID (Sticker Number)."""
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("""
        SELECT property_id FROM inventory 
        WHERE item_name = ? AND brand = ? AND quantity > 0 
        LIMIT 1
    """, (name, brand))
    result = cursor.fetchone(); conn.close()
    return result[0] if result else "N/A"

# --- REQUEST LOGIC ---

def add_request(name, items_dict, purpose):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("INSERT INTO requests (student_name, items_json, purpose) VALUES (?, ?, ?)", 
              (name, json.dumps(items_dict), purpose))
    conn.commit(); conn.close()

def get_all_requests():
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("SELECT * FROM requests ORDER BY id DESC"); r = c.fetchall(); conn.close()
    return r

def update_request_status(req_id, status):
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("UPDATE requests SET status = ? WHERE id = ?", (status, req_id))
    conn.commit(); conn.close()