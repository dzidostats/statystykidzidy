import asyncio
import aiohttp
import json
import random
import time
import os

BASE_URL = "https://jbzd.com.pl/mikroblog/user/profile/{}"
HEADERS = {"User-Agent": "Mozilla/5.0"}

CONCURRENCY = 2

active_true = []
active_false = []
banned = []

queue = asyncio.Queue()

TOTAL = 1000
PARTS = int(os.getenv("PARTS", "1"))
PART = int(os.getenv("PART", "0"))

chunk = TOTAL // PARTS

start = PART * chunk + 1
end = (PART + 1) * chunk

for i in range(start, end):
    queue.put_nowait(i)


async def worker(session):
    while True:
        try:
            user_id = queue.get_nowait()
        except asyncio.QueueEmpty:
            break

        try:
            async with session.get(BASE_URL.format(user_id), headers=HEADERS) as r:
                if r.status != 200:
                    print(f"ID {user_id} -> {r.status}")
                    continue

                data = await r.json()
                user = data.get("user", {})

                uid = user.get("id", user_id)
                is_active = user.get("active")
                is_banned = user.get("banned")

                print(f"ID {uid} -> active={is_active}, banned={is_banned}")

                item = {"id": uid}

                # 🔥 BAN
                if is_banned:
                    banned.append(item)

                # 🔥 ACTIVE TRUE / FALSE
                if is_active is True:
                    active_true.append(item)
                elif is_active is False:
                    active_false.append(item)

        except Exception as e:
            print("Błąd:", user_id, e)

        await asyncio.sleep(random.uniform(0.12, 0.12))
        queue.task_done()


async def main():
    start_time = time.time()

    connector = aiohttp.TCPConnector(limit=CONCURRENCY)

    async with aiohttp.ClientSession(connector=connector) as session:
        workers = [worker(session) for _ in range(CONCURRENCY)]
        await asyncio.gather(*workers)

    part = PART

    with open(f"active_true_{part}.json", "w") as f:
        json.dump(active_true, f, indent=2)

    with open(f"active_false_{part}.json", "w") as f:
        json.dump(active_false, f, indent=2)

    with open(f"banned_{part}.json", "w") as f:
        json.dump(banned, f, indent=2)

    print("active_true:", len(active_true))
    print("active_false:", len(active_false))
    print("banned:", len(banned))
    print("Czas:", time.time() - start_time)


asyncio.run(main())
