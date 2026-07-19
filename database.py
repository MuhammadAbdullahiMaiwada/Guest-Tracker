import sqlite3
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

DB_NAME = "guest.db"


def connect_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def create_table():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS guests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            purpose TEXT NOT NULL,
            room TEXT NOT NULL,
            host TEXT,
            phone TEXT,
            id_type TEXT,
            check_in TEXT NOT NULL,
            check_out TEXT
        )
    """)
    conn.commit()
    conn.close()


def add_guest(name, purpose, room, host="", phone="", id_type=""):
    conn = connect_db()
    cursor = conn.cursor()
    check_in = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO guests (name, purpose, room, host, phone, id_type, check_in) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (name, purpose, room, host, phone, id_type, check_in),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def check_out_guest(guest_id):
    conn = connect_db()
    cursor = conn.cursor()
    check_out_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "UPDATE guests SET check_out = ? WHERE id = ? AND check_out IS NULL",
        (check_out_time, guest_id),
    )
    conn.commit()
    updated = cursor.rowcount
    conn.close()
    return check_out_time if updated else None


def get_all_guests():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, purpose, room, host, phone, id_type, check_in, check_out FROM guests ORDER BY id DESC"
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_active_guests():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, purpose, room, host, phone, id_type, check_in, check_out FROM guests WHERE check_out IS NULL ORDER BY id DESC"
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_guests_by_range(range_filter="all"):
    conn = connect_db()
    cursor = conn.cursor()
    now = datetime.now()

    if range_filter == "today":
        since = now.strftime("%Y-%m-%d 00:00:00")
    elif range_filter == "week":
        since = (now - timedelta(days=7)).strftime("%Y-%m-%d 00:00:00")
    elif range_filter == "month":
        since = (now - timedelta(days=30)).strftime("%Y-%m-%d 00:00:00")
    else:
        since = None

    if since:
        cursor.execute(
            "SELECT id, name, purpose, room, host, phone, id_type, check_in, check_out FROM guests WHERE check_in >= ? ORDER BY id DESC",
            (since,),
        )
    else:
        cursor.execute(
            "SELECT id, name, purpose, room, host, phone, id_type, check_in, check_out FROM guests ORDER BY id DESC"
        )

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_checkins_last_7_days():
    conn = connect_db()
    cursor = conn.cursor()
    results = []
    for i in range(6, -1, -1):
        day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        cursor.execute(
            "SELECT COUNT(*) as cnt FROM guests WHERE check_in LIKE ?",
            (day + "%",),
        )
        row = cursor.fetchone()
        results.append({"date": day, "count": row["cnt"]})
    conn.close()
    return results


def get_stats():
    conn = connect_db()
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")

    cursor.execute("SELECT COUNT(*) as cnt FROM guests")
    total = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM guests WHERE check_out IS NULL")
    active = cursor.fetchone()["cnt"]

    cursor.execute("SELECT COUNT(*) as cnt FROM guests WHERE check_in LIKE ?", (today + "%",))
    today_count = cursor.fetchone()["cnt"]

    cursor.execute("""
        SELECT ROUND(AVG((JULIANDAY(check_out) - JULIANDAY(check_in)) * 1440)) as avg_min
        FROM guests WHERE check_out IS NOT NULL
    """)
    avg_row = cursor.fetchone()
    avg_minutes = int(avg_row["avg_min"]) if avg_row["avg_min"] else 0
    avg_stay = f"{avg_minutes // 60}h {avg_minutes % 60}m" if avg_minutes else "N/A"

    cursor.execute("""
        SELECT purpose, COUNT(*) as cnt FROM guests
        GROUP BY purpose ORDER BY cnt DESC LIMIT 1
    """)
    common_row = cursor.fetchone()
    common_purpose = common_row["purpose"] if common_row else "N/A"

    cursor.execute("""
        SELECT strftime('%w', check_in) as dow, COUNT(*) as cnt
        FROM guests GROUP BY dow ORDER BY cnt DESC LIMIT 1
    """)
    busy_row = cursor.fetchone()
    days = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]
    busiest_day = days[int(busy_row["dow"])] if busy_row else "N/A"

    conn.close()
    return {
        "total": total,
        "active": active,
        "checked_out": total - active,
        "today": today_count,
        "avg_stay": avg_stay,
        "common_purpose": common_purpose,
        "busiest_day": busiest_day,
    }


# Admin

def create_admin_table():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def create_admin(username, password):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO admins (username, password) VALUES (?, ?)",
            (username, generate_password_hash(password)),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def verify_admin(username, password):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, password FROM admins WHERE username = ?", (username,))
    admin = cursor.fetchone()
    conn.close()
    if admin and check_password_hash(admin["password"], password):
        return admin["id"]
    return None


def admin_exists():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as cnt FROM admins")
    row = cursor.fetchone()
    conn.close()
    return row["cnt"] > 0