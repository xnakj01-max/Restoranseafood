# main.py: inisialisasi FastAPI dan registrasi router
from contextlib import asynccontextmanager

from fastapi import FastAPI

import database as db
from routes import menu, transaction


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_db()  # aman dipanggil tiap worker (CREATE TABLE IF NOT EXISTS)
    yield


app = FastAPI(title="API Restoran Seafood", version="1.0", lifespan=lifespan)
app.include_router(menu.router)
app.include_router(transaction.router)


@app.get("/", tags=["Root"])
async def root():
    return {"message": "API Restoran Seafood", "docs": "/docs"}