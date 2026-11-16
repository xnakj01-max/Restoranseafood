# locustfile.py: skenario beban
# Read : locust -f locustfile.py --host http://127.0.0.1:8000 --headless -u 20 -r 20 ReadUser
# Write: locust -f locustfile.py --host http://127.0.0.1:8000 --headless -u 10 -r 10 WriteUser
# Locust berhenti otomatis setelah jumlah request tercapai (100 read / 50 write).
import random
import time

from locust import HttpUser, constant, task

READ_LIMIT, WRITE_LIMIT = 100, 50
_count = {"read": 0, "write": 0}
_start = {}


def _allowed(user, kind, limit) -> bool:
    _start.setdefault(kind, time.time())
    if _count[kind] >= limit:
        if not _start.get(kind + "_done"):
            _start[kind + "_done"] = time.time()
            print(f"[{kind}] {limit} request selesai dalam {_start[kind + '_done'] - _start[kind]:.2f} detik")
        user.environment.runner.quit()
        return False
    _count[kind] += 1
    return True


class ReadUser(HttpUser):
    wait_time = constant(0)

    @task
    def get_menu(self):
        if _allowed(self, "read", READ_LIMIT):
            self.client.get("/menu?skip=0&limit=10")


class WriteUser(HttpUser):
    wait_time = constant(0)

    @task
    def post_transaction(self):
        if _allowed(self, "write", WRITE_LIMIT):
            # menu 11-14 = minuman, stok besar sehingga tidak habis saat benchmark
            self.client.post("/transactions", json={"item_id": random.randint(11, 14), "qty": 1})