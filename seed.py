# seed.py: isi data awal 14 menu restoran seafood (jalankan: python seed.py)
import asyncio
import database as db

MENU = [
    ("Kepiting Saus Asam Manis", "Kepiting", 65000, 20),
    ("Kepiting Saos Lada Hitam", "Kepiting", 65000, 20),
    ("Kepiting Saos Tiram", "Kepiting", 65000, 20),
    ("Aneka Kerang Dara", "Kerang", 33000, 30),
    ("Kerang Asam Manis", "Kerang", 33000, 30),
    ("Kerang Saos Tiram", "Kerang", 33000, 30),
    ("Kerang Lada Hitam", "Kerang", 33000, 30),
    ("Cumi Asam Pedas", "Cumi", 45000, 25),
    ("Cumi Saos Tiram", "Cumi", 45000, 25),
    ("Cumi Lada Hitam", "Cumi", 45000, 25),
    ("Teh Es", "Minuman", 5000, 500),
    ("Es Jeruk", "Minuman", 8000, 500),
    ("Es Kelapa", "Minuman", 10000, 500),
    ("Es Buah", "Minuman", 15000, 500),
]


async def main():
    await db.init_db()
    async with db.get_conn() as conn:  # reset supaya id mulai dari 1 lagi
        await conn.execute("DELETE FROM transactions")
        await conn.execute("DELETE FROM menu")
        await conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('menu','transactions')")
        await conn.executemany(
            "INSERT INTO menu (nama, kategori, harga, stok) VALUES (?, ?, ?, ?)", MENU
        )
        await conn.commit()
    print(f"Seed selesai: {len(MENU)} menu dimasukkan.")


if __name__ == "__main__":
    asyncio.run(main())