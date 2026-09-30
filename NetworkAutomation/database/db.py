
import sqlite3
import ipaddress
from pathlib import Path
from datetime import datetime


# ============================================================
# DATABASE CONFIG
# ============================================================

# Thư mục chứa file db.py
BASE_DIR = Path(__file__).resolve().parent

# Database nằm cùng thư mục database/
DB_PATH = BASE_DIR / "network_automation.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    """
    Tạo kết nối SQLite.
    """

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    return conn


# ============================================================
# DATABASE MIGRATION HELPERS
# ============================================================

def _get_table_columns(cursor, table_name):
    """
    Lấy danh sách tên cột hiện có của bảng.
    """

    cursor.execute(f"PRAGMA table_info({table_name})")

    rows = cursor.fetchall()

    return {
        row["name"]
        for row in rows
    }


def _add_column_if_missing(
    cursor,
    table_name,
    column_name,
    column_definition
):
    """
    Nếu bảng chưa có column thì tự động thêm.
    """

    columns = _get_table_columns(cursor, table_name)

    if column_name not in columns:
        cursor.execute(
            f"""
            ALTER TABLE {table_name}
            ADD COLUMN {column_name} {column_definition}
            """
        )


# ============================================================
# DEVICES TABLE MIGRATION
# ============================================================

def _migrate_devices_table(cursor):
    """
    Đảm bảo bảng devices có đầy đủ các column cần thiết.

    Dùng để xử lý database cũ bị thiếu:
        ip
        hostname
        mac
        status
        duration
        first_seen
        last_seen
    """

    # --------------------------------------------------------
    # Nếu chưa có bảng devices thì tạo mới
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT UNIQUE,
            hostname TEXT,
            mac TEXT,
            status TEXT,
            duration REAL,
            first_seen TEXT,
            last_seen TEXT
        )
    """)

    # --------------------------------------------------------
    # Migration database cũ
    # --------------------------------------------------------

    _add_column_if_missing(
        cursor,
        "devices",
        "ip",
        "TEXT"
    )

    _add_column_if_missing(
        cursor,
        "devices",
        "hostname",
        "TEXT"
    )

    _add_column_if_missing(
        cursor,
        "devices",
        "mac",
        "TEXT"
    )

    _add_column_if_missing(
        cursor,
        "devices",
        "status",
        "TEXT"
    )

    _add_column_if_missing(
        cursor,
        "devices",
        "duration",
        "REAL"
    )

    _add_column_if_missing(
        cursor,
        "devices",
        "first_seen",
        "TEXT"
    )

    _add_column_if_missing(
        cursor,
        "devices",
        "last_seen",
        "TEXT"
    )

    # --------------------------------------------------------
    # Cập nhật dữ liệu NULL
    # --------------------------------------------------------

    columns = _get_table_columns(cursor, "devices")

    # Older schemas kept addresses under different column names. Adding a
    # new column alone does not copy their values into it.
    for target, aliases in {
        "ip": ("ip_address", "ip_addr", "address"),
        "mac": ("mac_address", "mac_addr"),
    }.items():
        for alias in aliases:
            if alias not in columns:
                continue
            rows = cursor.execute(
                f'SELECT id, "{alias}" AS value FROM devices '
                f'WHERE "{target}" IS NULL OR '
                f'LOWER(TRIM("{target}")) IN (\'\', \'none\', \'null\')'
            ).fetchall()
            for row in rows:
                value = str(row["value"] or "").strip()
                if not value or value.lower() in ("none", "null"):
                    continue
                if target == "ip":
                    try:
                        value = str(ipaddress.ip_address(value))
                    except ValueError:
                        continue
                # Do not delete or merge records to resolve a UNIQUE conflict.
                cursor.execute("SAVEPOINT address_copy")
                try:
                    cursor.execute(
                        f'UPDATE devices SET "{target}" = ? WHERE id = ?',
                        (value, row["id"]),
                    )
                except sqlite3.IntegrityError:
                    cursor.execute("ROLLBACK TO address_copy")
                finally:
                    cursor.execute("RELEASE address_copy")

    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    if "status" in columns:
        cursor.execute("""
            UPDATE devices
            SET status = 'Unknown'
            WHERE status IS NULL
               OR TRIM(status) = ''
        """)

    if "first_seen" in columns:
        cursor.execute("""
            UPDATE devices
            SET first_seen = ?
            WHERE first_seen IS NULL
               OR TRIM(first_seen) = ''
        """, (now,))

    if "last_seen" in columns:
        cursor.execute("""
            UPDATE devices
            SET last_seen = ?
            WHERE last_seen IS NULL
               OR TRIM(last_seen) = ''
        """, (now,))


# ============================================================
# INIT DATABASE
# ============================================================

def init_database():
    """
    Tạo database và các bảng.

    Đồng thời migration database cũ.
    """

    conn = get_connection()
    cursor = conn.cursor()

    try:

        # ----------------------------------------------------
        # Devices
        # ----------------------------------------------------

        _migrate_devices_table(cursor)

        # ----------------------------------------------------
        # Network Scans
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS network_scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT,
                hostname TEXT,
                mac TEXT,
                status TEXT,
                duration REAL,
                scan_time TEXT
            )
        """)

        # ----------------------------------------------------
        # Ping Results
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ping_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT,
                status TEXT,
                response REAL,
                ping_time TEXT
            )
        """)

        # ----------------------------------------------------
        # Network Devices
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS network_devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                ip TEXT,
                device_type TEXT,
                vendor TEXT,
                location TEXT,
                status TEXT,
                note TEXT
            )
        """)

        # Migration cho các bản NMS mới: Auto Discovery cần hai cột này.
        _add_column_if_missing(cursor, "network_devices", "created_at", "TEXT")
        _add_column_if_missing(cursor, "network_devices", "updated_at", "TEXT")

        now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "UPDATE network_devices SET created_at=? WHERE created_at IS NULL OR TRIM(created_at)=''",
            (now_text,)
        )
        cursor.execute(
            "UPDATE network_devices SET updated_at=COALESCE(NULLIF(updated_at,''), created_at) "
            "WHERE updated_at IS NULL OR TRIM(updated_at)=''"
        )

        # ----------------------------------------------------
        # Alerts
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT,
                alert_type TEXT,
                message TEXT,
                created_at TEXT,
                status TEXT
            )
        """)

        _add_column_if_missing(cursor, "alerts", "severity", "TEXT DEFAULT 'Warning'")
        cursor.execute("UPDATE alerts SET severity='Warning' WHERE severity IS NULL OR TRIM(severity)=''")

        # ----------------------------------------------------
        # Activity Logs
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT,
                description TEXT,
                created_at TEXT
            )
        """)

        # ----------------------------------------------------
        # Settings
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE,
                value TEXT
            )
        """)

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# ============================================================
# DEVICE CRUD
# ============================================================

# ------------------------------------------------------------
# CREATE DEVICE
# ------------------------------------------------------------

def create_device(
    ip,
    hostname="",
    mac="",
    status="Unknown",
    duration=None
):
    """
    Thêm thiết bị mới.

    Return:
        device_id nếu thành công
        None nếu IP đã tồn tại
    """

    init_database()

    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    try:

        cursor.execute("""
            INSERT INTO devices (
                ip,
                hostname,
                mac,
                status,
                duration,
                first_seen,
                last_seen
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            ip,
            hostname,
            mac,
            status,
            duration,
            now,
            now
        ))

        conn.commit()

        return cursor.lastrowid

    except sqlite3.IntegrityError:
        conn.rollback()
        return None

    finally:
        conn.close()


# ------------------------------------------------------------
# GET ALL DEVICES
# ------------------------------------------------------------

def get_all_devices():
    """
    Lấy toàn bộ thiết bị.
    """

    init_database()

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT
                id,
                ip,
                hostname,
                mac,
                status,
                duration,
                first_seen,
                last_seen
            FROM devices
            ORDER BY id ASC
        """)

        rows = cursor.fetchall()

        return [dict(row) for row in rows]

    finally:
        conn.close()


# ------------------------------------------------------------
# GET DEVICE
# ------------------------------------------------------------

def get_device(device_id):
    """
    Lấy thiết bị theo ID.
    """

    init_database()

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT
                id,
                ip,
                hostname,
                mac,
                status,
                duration,
                first_seen,
                last_seen
            FROM devices
            WHERE id = ?
        """, (device_id,))

        row = cursor.fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        conn.close()


# ------------------------------------------------------------
# GET DEVICE BY IP
# ------------------------------------------------------------

def get_device_by_ip(ip):
    """
    Lấy thiết bị theo IP.
    """

    init_database()

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT
                id,
                ip,
                hostname,
                mac,
                status,
                duration,
                first_seen,
                last_seen
            FROM devices
            WHERE ip = ?
        """, (ip,))

        row = cursor.fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        conn.close()


# ------------------------------------------------------------
# SEARCH DEVICES
# ------------------------------------------------------------

def search_devices(keyword=""):
    """
    Tìm thiết bị theo:
        IP
        Hostname
        MAC
    """

    init_database()

    conn = get_connection()
    cursor = conn.cursor()

    try:

        keyword = f"%{keyword}%"

        cursor.execute("""
            SELECT
                id,
                ip,
                hostname,
                mac,
                status,
                duration,
                first_seen,
                last_seen
            FROM devices
            WHERE
                ip LIKE ?
                OR hostname LIKE ?
                OR mac LIKE ?
            ORDER BY id ASC
        """, (
            keyword,
            keyword,
            keyword
        ))

        rows = cursor.fetchall()

        return [dict(row) for row in rows]

    finally:
        conn.close()


# ------------------------------------------------------------
# GET DEVICES BY STATUS
# ------------------------------------------------------------

def get_devices_by_status(status):
    """
    Lấy thiết bị theo status.
    """

    init_database()

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT
                id,
                ip,
                hostname,
                mac,
                status,
                duration,
                first_seen,
                last_seen
            FROM devices
            WHERE status = ?
            ORDER BY id ASC
        """, (status,))

        rows = cursor.fetchall()

        return [dict(row) for row in rows]

    finally:
        conn.close()


# ------------------------------------------------------------
# UPDATE DEVICE
# ------------------------------------------------------------

def update_device(
    device_id,
    ip=None,
    hostname=None,
    mac=None,
    status=None,
    duration=None
):
    """
    Cập nhật thiết bị.

    Chỉ cập nhật những giá trị được truyền vào.
    """

    init_database()

    device = get_device(device_id)

    if device is None:
        return False

    new_ip = (
        device["ip"]
        if ip is None
        else ip
    )

    new_hostname = (
        device["hostname"]
        if hostname is None
        else hostname
    )

    new_mac = (
        device["mac"]
        if mac is None
        else mac
    )

    new_status = (
        device["status"]
        if status is None
        else status
    )

    new_duration = (
        device["duration"]
        if duration is None
        else duration
    )

    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            UPDATE devices
            SET
                ip = ?,
                hostname = ?,
                mac = ?,
                status = ?,
                duration = ?,
                last_seen = ?
            WHERE id = ?
        """, (
            new_ip,
            new_hostname,
            new_mac,
            new_status,
            new_duration,
            now,
            device_id
        ))

        conn.commit()

        return cursor.rowcount > 0

    except sqlite3.IntegrityError:

        conn.rollback()

        return False

    finally:
        conn.close()


# ------------------------------------------------------------
# DELETE DEVICE
# ------------------------------------------------------------

def delete_device(device_id):
    """
    Xóa thiết bị theo ID.
    """

    init_database()

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            DELETE FROM devices
            WHERE id = ?
        """, (device_id,))

        conn.commit()

        return cursor.rowcount > 0

    finally:
        conn.close()


# ------------------------------------------------------------
# DELETE DEVICE BY IP
# ------------------------------------------------------------

def delete_device_by_ip(ip):
    """
    Xóa thiết bị theo IP.
    """

    init_database()

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            DELETE FROM devices
            WHERE ip = ?
        """, (ip,))

        conn.commit()

        return cursor.rowcount > 0

    finally:
        conn.close()


# ============================================================
# NETWORK SCAN -> DEVICE DATABASE
# ============================================================

def save_devices(results):
    """Upsert by IP on both old and new schemas without erasing known data."""
    init_database()
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    columns = _get_table_columns(cursor, "devices")

    def text_value(record, *keys):
        for key in keys:
            value = record.get(key)
            if value is not None:
                value = str(value).strip()
                if value and value.lower() not in ("none", "null"):
                    return value
        return ""

    try:
        for result in results:
            if not isinstance(result, dict):
                continue
            ip = text_value(result, "ip", "ip_address", "ip_addr", "address")
            try:
                ip = str(ipaddress.ip_address(ip))
            except ValueError:
                continue
            hostname = text_value(result, "hostname", "host_name", "device_name")
            mac = text_value(result, "mac", "mac_address", "mac_addr")
            status = text_value(result, "status", "state") or "Unknown"
            duration = result.get("duration")
            existing = cursor.execute(
                "SELECT id, hostname, mac FROM devices WHERE ip = ?", (ip,)
            ).fetchall()
            if existing:
                for row in existing:
                    values = {
                        "hostname": hostname or row["hostname"] or "",
                        "mac": mac or row["mac"] or "",
                        "status": status, "duration": duration, "last_seen": now,
                    }
                    # Mirror old MAC columns when a new value is available.
                    if mac:
                        for alias in ("mac_address", "mac_addr"):
                            if alias in columns:
                                values[alias] = mac
                    assignments = ", ".join(f'"{key}" = ?' for key in values)
                    cursor.execute(
                        f"UPDATE devices SET {assignments} WHERE id = ?",
                        (*values.values(), row["id"]),
                    )
            else:
                values = {
                    "ip": ip, "hostname": hostname, "mac": mac,
                    "status": status, "duration": duration,
                    "first_seen": now, "last_seen": now,
                }
                # Legacy address columns can be NOT NULL / UNIQUE.
                for alias in ("ip_address", "ip_addr", "address"):
                    if alias in columns:
                        values[alias] = ip
                for alias in ("mac_address", "mac_addr"):
                    if alias in columns:
                        values[alias] = mac
                names = ", ".join(f'"{key}"' for key in values)
                placeholders = ", ".join("?" for _ in values)
                cursor.execute(
                    f"INSERT INTO devices ({names}) VALUES ({placeholders})",
                    tuple(values.values()),
                )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ============================================================
# DEVICE STATISTICS
# ============================================================

def get_device_statistics():
    """
    Thống kê thiết bị.

    Return:
        {
            "total": ...,
            "online": ...,
            "offline": ...
        }
    """

    init_database()

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM devices
        """)

        total = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) AS online
            FROM devices
            WHERE status = 'Online'
        """)

        online = cursor.fetchone()["online"]

        cursor.execute("""
            SELECT COUNT(*) AS offline
            FROM devices
            WHERE status = 'Offline'
        """)

        offline = cursor.fetchone()["offline"]

        return {
            "total": total,
            "online": online,
            "offline": offline
        }

    finally:
        conn.close()


# ============================================================
# ACTIVITY LOG
# ============================================================

def add_activity_log(action, description):
    """
    Ghi log hoạt động.
    """

    init_database()

    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    try:

        cursor.execute("""
            INSERT INTO activity_logs (
                action,
                description,
                created_at
            )
            VALUES (?, ?, ?)
        """, (
            action,
            description,
            now
        ))

        conn.commit()

    finally:
        conn.close()


# ============================================================
# INITIALIZE DATABASE
# ============================================================

# Khi import database.db,
# tự động tạo/migration database.
init_database()

