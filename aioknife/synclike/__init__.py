from .group import Group  # noqa
from .background import Background  # noqa

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

# Background
"""
from aioknife.synclike import Background

async def run(i):
    print("before", i)
    await asyncio.sleep(0.05)
    print("after", i)
    return i

with Background() as bk:
    bk.add(run, 0)
    bk.add(run, 1)
    bk.add(run, 2)

"""
