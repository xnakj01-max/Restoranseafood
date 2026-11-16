# test_race.py: atur stok menu id=1 menjadi 1, lalu kirim 2 request transaksi serentak
import asyncio
import httpx

BASE = "http://127.0.0.1:8000"


async def main():
    async with httpx.AsyncClient(timeout=30) as client:
        # Persiapan: stok menu id=1 dijadikan 1
        menu = (await client.get(f"{BASE}/menu/1")).json()
        await client.put(f"{BASE}/menu/1", json={
            "nama": menu["nama"], "kategori": menu["kategori"],
            "harga": menu["harga"], "stok": 1,
        })

        url = f"{BASE}/transactions"
        payload = {"item_id": 1, "qty": 1}
        # Dua request dikirim serentak
        res1, res2 = await asyncio.gather(
            client.post(url, json=payload), client.post(url, json=payload)
        )
        print("Respon Request 1:", res1.status_code, res1.json())
        print("Respon Request 2:", res2.status_code, res2.json())

        akhir = (await client.get(f"{BASE}/menu/1")).json()
        print("Stok akhir menu id=1:", akhir["stok"])


if __name__ == "__main__":
    asyncio.run(main())