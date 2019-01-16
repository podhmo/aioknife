import logging
import asyncio
import contextlib
from aioknife.aq import AQ
from aioknife.debug import Inspector
logger = logging.getLogger(__name__)
SENTINEL = object()


@contextlib.contextmanager
def executor(
    *,
    loop=None,
    q=None,
    concurrency=10,
    debug=False,
):
    loop = loop or asyncio.get_event_loop()
    q = q or asyncio.Queue()
    n = concurrency

    inspector = Inspector()
    aq = AQ(loop, q=q)

    futs = []

    def submit(afn, *args, **kwargs):
        fut = aq.add(afn, args=args, kwargs=kwargs)
        futs.append(fut)
        return fut

    yield submit

    teardown = lambda: None  # noqa
    if debug:
        w = loop.create_task(inspector.watch_queue(loop, q))
        teardown = w.cancel

    logger.info("start	concurrency:%d	queue:%s", n, inspector.format_queue(q))
    aq.start(n)
    try:
        aq.join()
    finally:
        teardown()

    logger.info("end	concurrency:%d	queue:%s", n, inspector.format_queue(q))

    for fut in futs:
        fut.result()
