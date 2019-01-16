from .group import Group  # noqa
from .executor import executor  # noqa

# TODO: documentation

# Group
"""
import asyncio
from aioknife.synclike import Group

async def run(i):
    await asyncio.sleep(0.05)
    return i

g = Group()
for i in range(10):
    g.go(run, i)
got = g.wait()
"""

# executor
"""
from aioknife.synclike import executor

async def run(i):
    print("before", i)
    await asyncio.sleep(0.05)
    print("after", i)
    return i

with executor() as submit:
    submit(run, 0)
    submit(run, 1)
    submit(run, 2)
"""
