import time
import asyncio


def req(i):
    print(i, "start[S]")
    time.sleep(0.5)
    print(i, "end  [S]")
    return i


async def req_await(i):
    print(i, "start[A]")
    await asyncio.sleep(0.5)
    print(i, "end  [A]")
    return i
