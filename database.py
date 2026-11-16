# database.py: koneksi aiosqlite + inisialisasi tabel + seluruh query (async, non-blocking)
import os
from datetime import datetime
from typing import Optional

import aiosqlite

DB_PATH = os.getenv("DB_PATH", "seafood.db")

# Catatan: kolom `stok` sengaja TIDAK diberi CHECK (stok >= 0) agar Tahap 1
# pada B3 (tanpa lock) bisa memperlihatkan stok negatif (overselling).
# Validasi stok >= 0 tetap dilakukan lewat Pydantic (Field ge=0) dan logika bisnis.
CREATE_MENU_TABLE = """
CREATE TABLE IF NOT EXISTS menu (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    nama     TEXT NOT NULL,
    kategori TEXT NOT NULL,
    harga    REAL NOT NULL,
    stok     INTEGER NOT NULL          -- kolom kuantitas wajib
);
"""

CREATE_TRX_TABLE = """
CREATE TABLE IF NOT EXISTS transactions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id     INTEGER NOT NULL,
    qty         INTEGER NOT NULL,
    total_harga REAL NOT NULL,
    status      TEXT NOT NULL,         -- pending | processing | completed | failed
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
"""


def get_conn() -> aiosqlite.Connection:
    """Buat koneksi baru per operasi. timeout=30 mencegah 'database is locked'
    saat beberapa worker Uvicorn (proses berbeda) menulis ke file SQLite yang sama."""
    return aiosqlite.connect(DB_PATH, timeout=30)


async def init_db() -> None:
    async with get_conn() as db:
        await db.execute("PRAGMA journal_mode=WAL;")  # baca/tulis lebih konkuren
        await db.execute(CREATE_MENU_TABLE)
        await db.execute(CREATE_TRX_TABLE)
        await db.commit()


# ---------------- CRUD menu ----------------
async def list_menu(skip: int, limit: int) -> list[dict]:
    async with get_conn() as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM menu ORDER BY id LIMIT ? OFFSET ?", (limit, skip))
        return [dict(r) for r in await cur.fetchall()]


async def get_menu(menu_id: int) -> Optional[dict]:
    async with get_conn() as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM menu WHERE id = ?", (menu_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def insert_menu(nama: str, kategori: str, harga: float, stok: int) -> int:
    async with get_conn() as db:
        cur = await db.execute(
            "INSERT INTO menu (nama, kategori, harga, stok) VALUES (?, ?, ?, ?)",
            (nama, kategori, harga, stok),
        )
        await db.commit()
        return cur.lastrowid


async def update_menu(menu_id: int, nama: str, kategori: str, harga: float, stok: int) -> bool:
    async with get_conn() as db:
        cur = await db.execute(
            "UPDATE menu SET nama=?, kategori=?, harga=?, stok=? WHERE id=?",
            (nama, kategori, harga, stok, menu_id),
        )
        await db.commit()
        return cur.rowcount > 0


async def delete_menu(menu_id: int) -> bool:
    """Hard delete: baris dihapus permanen dari basis data."""
    async with get_conn() as db:
        cur = await db.execute("DELETE FROM menu WHERE id = ?", (menu_id,))
        await db.commit()
        return cur.rowcount > 0


# ---------------- stok ----------------
async def get_stok(menu_id: int) -> Optional[int]:
    async with get_conn() as db:
        cur = await db.execute("SELECT stok FROM menu WHERE id = ?", (menu_id,))
        row = await cur.fetchone()
        return row[0] if row else None


async def decrement_stok(menu_id: int, qty: int) -> None:
    async with get_conn() as db:
        await db.execute("UPDATE menu SET stok = stok - ? WHERE id = ?", (qty, menu_id))
        await db.commit()


async def increment_stok(menu_id: int, qty: int) -> None:
    """Dipakai untuk mengembalikan stok jika transaksi gagal."""
    async with get_conn() as db:
        await db.execute("UPDATE menu SET stok = stok + ? WHERE id = ?", (qty, menu_id))
        await db.commit()


# ---------------- transaksi ----------------
def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


async def insert_transaction(item_id: int, qty: int, total_harga: float, status: str = "pending") -> int:
    async with get_conn() as db:
        cur = await db.execute(
            "INSERT INTO transactions (item_id, qty, total_harga, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (item_id, qty, total_harga, status, _now(), _now()),
        )
        await db.commit()
        return cur.lastrowid


async def update_trx_status(trx_id: int, status: str) -> None:
    async with get_conn() as db:
        await db.execute(
            "UPDATE transactions SET status=?, updated_at=? WHERE id=?", (status, _now(), trx_id)
        )
        await db.commit()


async def get_transaction(trx_id: int) -> Optional[dict]:
    async with get_conn() as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM transactions WHERE id = ?", (trx_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def list_transactions(status: Optional[str], skip: int, limit: int) -> list[dict]:
    async with get_conn() as db:
        db.row_factory = aiosqlite.Row
        if status:
            cur = await db.execute(
                "SELECT * FROM transactions WHERE status=? ORDER BY id DESC LIMIT ? OFFSET ?",
                (status, limit, skip),
            )
        else:
            cur = await db.execute(
                "SELECT * FROM transactions ORDER BY id DESC LIMIT ? OFFSET ?", (limit, skip)
            )
        return [dict(r) for r in await cur.fetchall()]