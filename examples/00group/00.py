import logging
import time
from aioknife import Group
import fakes

logging.basicConfig(level=logging.DEBUG)
st = time.time()
g = Group(limit=5)
for i in range(10):
    g.go(fakes.req, i)
    g.go(fakes.req_await, i)
print(g.wait())
print(time.time() - st)
