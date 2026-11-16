Video Presentasi: https://youtu.be/XXXXXXXX

# API Restoran Seafood
Nama : Agung Suryansyah
NIM  : 231220112
Tema: Restoran Seafood (resource: menu, transaksi: transactions)

## Instalasi
pip install -r requirements.txt
python seed.py

## Menjalankan
uvicorn main:app --port 8000          # 1 worker
uvicorn main:app --workers 4 --port 8000   # 4 worker
Dokumentasi: http://127.0.0.1:8000/docs

## Uji Race Condition (B3)
# Tahap 1 (tanpa lock):  set USE_LOCK=0   (PowerShell: $env:USE_LOCK="0")
# Tahap 2 (dengan lock): set USE_LOCK=1
python test_race.py

## Uji Beban (Locust)
locust -f locustfile.py --host http://127.0.0.1:8000 --headless -u 20 -r 20 ReadUser
locust -f locustfile.py --host http://127.0.0.1:8000 --headless -u 10 -r 10 WriteUser