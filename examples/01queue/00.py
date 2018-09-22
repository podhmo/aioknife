import asyncio
import time
import logging
from aioknife.synclike import Background
logger = logging.getLogger(__name__)


async def consume_async(i, level):
    logger.info("%s %s %s", i, level, "start[A]")
    await asyncio.sleep(0.5)
    logger.info("%s %s %s", i, level, "end[A]")
    return i, level + 1


logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s: %(message)s")
st = time.time()

r = []
with Background(concurrency=3) as q:
    for i in range(4):
        q.add(consume_async, i, 0)

    for v, level in q:
        r.append((v, level))
        if level < 3:
            for i in range(v):
                q.add(consume_async, i, level)
print(r)
print(len(r) * 0.5)
print(time.time() - st)
