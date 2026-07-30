import sqlite3
from pathlib import Path
from datetime import datetime


# ==========================================
# DATABASE CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

DATABASE_FILE = BASE_DIR / "database.db"


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_connection():

    connection = sqlite3.connect(
        str(DATABASE_FILE)
    )

    connection.row_factory = sqlite3.Row

    return connection


# ==========================================
# INITIALIZE DATABASE
# ==========================================

def init_database():

    connection = get_connection()

    cursor = connection.cursor()


    # ======================================
    # USERS TABLE
    # ======================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (

            user_id INTEGER PRIMARY KEY,

            username TEXT DEFAULT '',

            first_name TEXT DEFAULT '',

            status TEXT DEFAULT 'pending',

            created_at TEXT DEFAULT ''

        )
        """
    )


    # ======================================
    # FILES TABLE
    # ======================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS files (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            filename TEXT NOT NULL,

            file_path TEXT NOT NULL,

            uploaded_at TEXT NOT NULL,

            status TEXT DEFAULT 'stopped',

            pid INTEGER DEFAULT NULL,

            log_path TEXT DEFAULT '',

            FOREIGN KEY (user_id)
                REFERENCES users(user_id)

        )
        """
    )


    # ======================================
    # PROXIES TABLE
    # ======================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS proxies (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            proxy TEXT NOT NULL,

            created_at TEXT NOT NULL

        )
        """
    )


    connection.commit()

    connection.close()


# ==========================================
# USER FUNCTIONS
# ==========================================

def add_user(
    user_id,
    username="",
    first_name=""
):

    connection = get_connection()

    cursor = connection.cursor()


    now = datetime.now().strftime(

        "%Y-%m-%d %H:%M:%S"

    )


    cursor.execute(

        """
        INSERT OR IGNORE INTO users
        (
            user_id,
            username,
            first_name,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,

        (
            int(user_id),
            username or "",
            first_name or "",
            "pending",
            now
        )

    )


    # Update user information
    cursor.execute(

        """
        UPDATE users

        SET username = ?,
            first_name = ?

        WHERE user_id = ?

        """,

        (
            username or "",
            first_name or "",
            int(user_id)
        )

    )


    connection.commit()

    connection.close()


def get_user_status(user_id):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(

        """
        SELECT status

        FROM users

        WHERE user_id = ?

        """,

        (int(user_id),)

    )


    row = cursor.fetchone()


    connection.close()


    if row is None:

        return None


    return row["status"]


def set_user_status(
    user_id,
    status
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(

        """
        UPDATE users

        SET status = ?

        WHERE user_id = ?

        """,

        (
            status,
            int(user_id)
        )

    )


    changed = cursor.rowcount > 0


    connection.commit()

    connection.close()


    return changed


def get_pending_users():

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(

        """
        SELECT
            user_id,
            username,
            first_name,
            status,
            created_at

        FROM users

        WHERE status = 'pending'

        ORDER BY created_at ASC

        """

    )


    rows = cursor.fetchall()


    connection.close()


    return rows


def get_approved_users():

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(

        """
        SELECT
            user_id,
            username,
            first_name,
            status,
            created_at

        FROM users

        WHERE status = 'approved'

        ORDER BY created_at ASC

        """

    )


    rows = cursor.fetchall()


    connection.close()


    return rows


def get_blocked_users():

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(

        """
        SELECT
            user_id,
            username,
            first_name,
            status,
            created_at

        FROM users

        WHERE status = 'blocked'

        ORDER BY created_at ASC

        """

    )


    rows = cursor.fetchall()


    connection.close()


    return rows


# ==========================================
# FILE FUNCTIONS
# ==========================================

def add_file(

    user_id,

    filename,

    file_path,

    log_path=""

):

    # Try to insert, but if the table doesn't exist -> initialize DB and retry once.
    try:
        connection = get_connection()
        cursor = connection.cursor()

        uploaded_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            """
            INSERT INTO files
            (
                user_id,
                filename,
                file_path,
                uploaded_at,
                status,
                pid,
                log_path
            )

            VALUES (?, ?, ?, ?, ?, ?, ?)

            """,
            (
                int(user_id),
                filename,
                str(file_path),
                uploaded_at,
                "stopped",
                None,
                str(log_path or "")
            )
        )

        file_id = cursor.lastrowid

        connection.commit()
        connection.close()

        return file_id

    except sqlite3.OperationalError as e:
        if "no such table" in str(e).lower():
            # Initialize DB and retry once
            try:
                init_database()
                connection = get_connection()
                cursor = connection.cursor()

                uploaded_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                cursor.execute(
                    """
                    INSERT INTO files
                    (
                        user_id,
                        filename,
                        file_path,
                        uploaded_at,
                        status,
                        pid,
                        log_path
                    )

                    VALUES (?, ?, ?, ?, ?, ?, ?)

                    """,
                    (
                        int(user_id),
                        filename,
                        str(file_path),
                        uploaded_at,
                        "stopped",
                        None,
                        str(log_path or "")
                    )
                )

                file_id = cursor.lastrowid
                connection.commit()
                connection.close()
                return file_id
            except Exception:
                try:
                    connection.close()
                except Exception:
                    pass
                return None
        else:
            raise


def get_user_files(user_id):

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                user_id,
                filename,
                file_path,
                uploaded_at,
                status,
                pid,
                log_path

            FROM files

            WHERE user_id = ?

            ORDER BY uploaded_at DESC

            """,
            (int(user_id),)
        )

        rows = cursor.fetchall()
        connection.close()
        return rows

    except sqlite3.OperationalError as e:
        if "no such table" in str(e).lower():
            init_database()
            return []
        raise


def get_file(
    file_id,
    user_id=None
):

    connection = get_connection()

    cursor = connection.cursor()


    if user_id is None:

        cursor.execute(

            """
            SELECT *

            FROM files

            WHERE id = ?

            """,

            (int(file_id),)

        )

    else:

        cursor.execute(

            """
            SELECT *

            FROM files

            WHERE id = ?

            AND user_id = ?

            """,

            (
                int(file_id),
                int(user_id)
            )

        )


    row = cursor.fetchone()


    connection.close()


    return row


def update_file_status(

    file_id,

    status

):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(

        """
        UPDATE files

        SET status = ?

        WHERE id = ?

        """,

        (
            status,
            int(file_id)
        )

    )


    connection.commit()

    connection.close()


def update_file_status_by_filename(

    filename,

    status

):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(

        """
        UPDATE files

        SET status = ?

        WHERE filename = ?

        """,

        (
            status,
            filename
        )

    )


    connection.commit()

    connection.close()


def update_file_pid(

    file_id,

    pid

):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(

        """
        UPDATE files

        SET pid = ?

        WHERE id = ?

        """,

        (
            pid,
            int(file_id)
        )

    )


    connection.commit()

    connection.close()


def delete_file(

    file_id,

    user_id

):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(

        """
        DELETE FROM files

        WHERE id = ?

        AND user_id = ?

        """,

        (
            int(file_id),
            int(user_id)
        )

    )


    deleted = cursor.rowcount > 0


    connection.commit()

    connection.close()


    return deleted


# ==========================================
# PROXY FUNCTIONS
# ==========================================

def add_proxy(

    user_id_or_proxy,

    proxy=None

):

    if proxy is None:

        proxy = user_id_or_proxy

        user_id = 0

    else:

        user_id = int(user_id_or_proxy)


    try:
        connection = get_connection()
        cursor = connection.cursor()

        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            """
            INSERT INTO proxies
            (
                user_id,
                proxy,
                created_at
            )

            VALUES (?, ?, ?)

            """,
            (
                int(user_id),
                proxy,
                created_at
            )
        )

        connection.commit()
        connection.close()
        return True

    except sqlite3.OperationalError as e:
        if "no such table" in str(e).lower():
            init_database()
            try:
                connection = get_connection()
                cursor = connection.cursor()
                created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute(
                    """
                    INSERT INTO proxies
                    (
                        user_id,
                        proxy,
                        created_at
                    )

                    VALUES (?, ?, ?)

                    """,
                    (
                        int(user_id),
                        proxy,
                        created_at
                    )
                )
                connection.commit()
                connection.close()
                return True
            except Exception:
                try:
                    connection.close()
                except Exception:
                    pass
                return False
        else:
            connection.rollback()
            connection.close()
            return False
    except Exception:
        try:
            connection.rollback()
        except Exception:
            pass
        try:
            connection.close()
        except Exception:
            pass
        return False


def get_all_proxies():

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *

            FROM proxies

            ORDER BY created_at DESC

            """

        )

        rows = cursor.fetchall()
        connection.close()
        return rows
    except sqlite3.OperationalError as e:
        if "no such table" in str(e).lower():
            init_database()
            return []
        raise


def get_proxies():

    return get_all_proxies()


def delete_proxy(

    proxy_id

):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(

        """
        DELETE FROM proxies

        WHERE id = ?

        """,

        (int(proxy_id),)

    )


    deleted = cursor.rowcount > 0


    connection.commit()

    connection.close()


    return deleted

# ==========================================
# AUTH COMPATIBILITY FUNCTIONS
# ==========================================

def is_approved(user_id):
    """
    Returns True if the user is approved.
    """

    status = get_user_status(user_id)

    return status == "approved"


def is_blocked(user_id):
    """
    Returns True if the user is blocked.
    """

    status = get_user_status(user_id)

    return status == "blocked"


def is_pending(user_id):
    """
    Returns True if the user is pending.
    """

    status = get_user_status(user_id)

    return status == "pending"
