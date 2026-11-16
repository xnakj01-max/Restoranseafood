# routes/menu.py: CRUD resource utama (menu restoran)
from fastapi import APIRouter, HTTPException, Query, status

import database as db
from models import MenuCreate, MenuOut

router = APIRouter(prefix="/menu", tags=["Menu"])


@router.get("", response_model=list[MenuOut])
async def list_menu(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100)):
    return await db.list_menu(skip, limit)


@router.get("/{menu_id}", response_model=MenuOut)
async def get_menu(menu_id: int):
    row = await db.get_menu(menu_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Menu tidak ditemukan")
    return row


@router.post("", response_model=MenuOut, status_code=status.HTTP_201_CREATED)
async def create_menu(data: MenuCreate):
    new_id = await db.insert_menu(data.nama, data.kategori, data.harga, data.stok)
    return await db.get_menu(new_id)


@router.put("/{menu_id}", response_model=MenuOut)
async def update_menu(menu_id: int, data: MenuCreate):
    ok = await db.update_menu(menu_id, data.nama, data.kategori, data.harga, data.stok)
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Menu tidak ditemukan")
    return await db.get_menu(menu_id)  # kembalikan data terbaru


@router.delete("/{menu_id}")
async def delete_menu(menu_id: int):
    ok = await db.delete_menu(menu_id)  # hard delete
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Menu tidak ditemukan")
    return {"message": f"Menu {menu_id} dihapus permanen"}