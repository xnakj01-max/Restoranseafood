# models.py: skema Pydantic (request & response)
from typing import Literal
from pydantic import BaseModel, Field


class MenuBase(BaseModel):
    nama: str = Field(min_length=1, max_length=100, examples=["Kepiting Saus Asam Manis"])
    kategori: str = Field(min_length=1, max_length=50, examples=["Kepiting"])
    harga: float = Field(gt=0, examples=[65000])
    stok: int = Field(ge=0, examples=[20])  # validasi ge=0 hanya untuk request masuk


class MenuCreate(MenuBase):
    pass


class MenuOut(BaseModel):
    # Response sengaja tidak mewarisi MenuBase: tanpa validasi ge=0, agar stok negatif
    # akibat race condition (demo B3 Tahap 1) tetap bisa ditampilkan, bukan error 500.
    id: int
    nama: str
    kategori: str
    harga: float
    stok: int


class TransactionCreate(BaseModel):
    item_id: int = Field(gt=0)
    qty: int = Field(gt=0)


class TransactionOut(BaseModel):
    id: int
    item_id: int
    qty: int
    total_harga: float
    status: Literal["pending", "processing", "completed", "failed"]
    created_at: str
    updated_at: str


class TransactionAccepted(BaseModel):
    id: int
    status: str
    message: str