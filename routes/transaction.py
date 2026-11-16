# routes/transaction.py: transaksi pesanan + pemrosesan asinkron + penguncian stok
import asyncio
import os
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status

import database as db
from models import TransactionAccepted, TransactionCreate, TransactionOut

router = APIRouter(prefix="/transactions", tags=["Transactions"])

# asyncio.Lock di tingkat modul: hanya SATU coroutine yang boleh berada di critical
# section pemotongan stok pada satu waktu (dalam satu event loop / satu proses worker).
stok_lock = asyncio.Lock()

# Saklar untuk demo B3: USE_LOCK=0 -> Tahap 1 (tanpa lock), USE_LOCK=1 -> Tahap 2 (dengan lock)
USE_LOCK = os.getenv("USE_LOCK", "1") == "1"


async def potong_stok_tanpa_lock(item_id: int, qty: int) -> bool:
    """VERSI 1 (rawan race condition): read -> sleep -> write tanpa pengaman."""
    stok_terkini = await db.get_stok(item_id)
    # Jeda artifisial: saat coroutine ini await, event loop memberi giliran ke request lain
    # yang juga membaca stok yang SAMA sebelum sempat dikurangi.
    await asyncio.sleep(0.01)
    if stok_terkini is None or stok_terkini < qty:
        return False
    await db.decrement_stok(item_id, qty)
    return True


async def potong_stok_dengan_lock(item_id: int, qty: int) -> bool:
    """VERSI 2 (aman): seluruh read-check-write dibungkus asyncio.Lock."""
    async with stok_lock:  # request lain menunggu di sini sampai lock dilepas
        stok_terkini = await db.get_stok(item_id)
        await asyncio.sleep(0.01)
        if stok_terkini is None or stok_terkini < qty:
            return False
        await db.decrement_stok(item_id, qty)
        return True


async def potong_stok(item_id: int, qty: int) -> bool:
    return await (potong_stok_dengan_lock if USE_LOCK else potong_stok_tanpa_lock)(item_id, qty)


# Fungsi pekerja internal latar belakang (BUKAN endpoint HTTP).
# Dijalankan FastAPI setelah respon pending dikirim ke klien.
async def proses_transaksi_background(trx_id: int, item_id: int, qty: int) -> None:
    try:
        await db.update_trx_status(trx_id, "processing")
        await asyncio.sleep(3)  # simulasi pekerjaan I/O (mis. dapur menyiapkan pesanan)
        await db.update_trx_status(trx_id, "completed")
    except Exception:
        # Jika gagal: tandai failed dan kembalikan stok yang sudah dipotong
        await db.update_trx_status(trx_id, "failed")
        await db.increment_stok(item_id, qty)


@router.post("", response_model=TransactionAccepted, status_code=status.HTTP_202_ACCEPTED)
async def create_transaction(data: TransactionCreate, bg: BackgroundTasks):
    menu = await db.get_menu(data.item_id)
    if not menu:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Menu tidak terdaftar")

    # Potong stok secara aman; jika stok tidak cukup -> 409 Conflict
    if not await potong_stok(data.item_id, data.qty):
        raise HTTPException(status.HTTP_409_CONFLICT, "Stok habis atau tidak mencukupi")

    trx_id = await db.insert_transaction(
        data.item_id, data.qty, menu["harga"] * data.qty, status="pending"
    )
    # Jadwalkan pekerjaan latar belakang; respon langsung dikirim tanpa menunggu 3 detik
    bg.add_task(proses_transaksi_background, trx_id, data.item_id, data.qty)
    return {"id": trx_id, "status": "pending", "message": "Transaksi diproses"}


@router.get("", response_model=list[TransactionOut])
async def list_transactions(
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    return await db.list_transactions(status_filter, skip, limit)


@router.get("/{trx_id}", response_model=TransactionOut)
async def get_transaction(trx_id: int):
    row = await db.get_transaction(trx_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Transaksi tidak ditemukan")
    return row