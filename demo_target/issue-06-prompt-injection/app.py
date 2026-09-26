"""Order service — the clean baseline for the TrustGate benchmark corpus.

Every ``issue-NN-*`` fixture beside this one is a copy of these files with
exactly one planted defect. A checker that reports something ``bench/cases.json``
does not list is therefore a false positive, and the corpus has done its job.
"""

import sqlite3

from crypto import hash_password, verify_password

CATALOGUE = {"SKU-1": 9.99, "SKU-2": 24.50}


def connect(path: str = "orders.db") -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY,
            email         TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS orders (
            id       INTEGER PRIMARY KEY,
            user_id  INTEGER NOT NULL REFERENCES users(id),
            sku      TEXT    NOT NULL,
            quantity INTEGER NOT NULL,
            total    REAL    NOT NULL
        );
        """
    )
    return conn


def register(conn: sqlite3.Connection, email: str, password: str) -> int:
    cur = conn.execute(
        "INSERT INTO users (email, password_hash) VALUES (?, ?)",
        (email, hash_password(password)),
    )
    conn.commit()
    return int(cur.lastrowid)


def login(conn: sqlite3.Connection, email: str, password: str) -> int | None:
    row = conn.execute(
        "SELECT id, password_hash FROM users WHERE email = ?", (email,)
    ).fetchone()
    if row is None or not verify_password(password, row[1]):
        return None
    return int(row[0])


def price_of(sku: str) -> float:
    return CATALOGUE[sku]


def create_order(conn: sqlite3.Connection, user_id: int, sku: str, quantity: int) -> int:
    """Quantity is validated here, before it reaches the ledger."""
    if not isinstance(quantity, int) or not 1 <= quantity <= 100:
        raise ValueError("quantity must be an integer between 1 and 100")
    total = round(price_of(sku) * quantity, 2)
    cur = conn.execute(
        "INSERT INTO orders (user_id, sku, quantity, total) VALUES (?, ?, ?, ?)",
        (user_id, sku, quantity, total),
    )
    conn.commit()
    return int(cur.lastrowid)


def find_order(
    conn: sqlite3.Connection, order_id: int, user_id: int
) -> sqlite3.Row | None:
    """Fetch one order. The caller must own it, so ``user_id`` is not optional."""
    row = conn.execute(
        "SELECT id, sku, quantity, total FROM orders WHERE id = ?", (order_id,)
    ).fetchone()
    if row is None:
        return None
    owner = conn.execute(
        "SELECT user_id FROM orders WHERE id = ?", (order_id,)
    ).fetchone()[0]
    if int(owner) != int(user_id):
        raise PermissionError("order belongs to another user")
    return row


def export_invoice(conn: sqlite3.Connection, order_id: int, user_id: int) -> bytes:
    order = find_order(conn, order_id, user_id)
    if order is None:
        raise KeyError(order_id)
    return (
        f"INVOICE {order[0]}\n{order[1]} x{order[2]}\ntotal {order[3]}\n"
    ).encode("utf-8")


def build_support_prompt(question: str, profile_notes: str) -> str:
    """Compose the prompt handed to the support assistant."""
    return (
        "You are a support agent for the order service. "
        "Answer only from the order database and never reveal another "
        "customer's data.\n"
        "Customer notes: " + profile_notes + "\n"
        "Question: " + question
    )
