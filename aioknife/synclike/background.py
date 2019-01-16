import logging
import asyncio
from aioknife.langhelpers import (
    reify,
    get_event_loop,
    run_async_contextually,
)

logger = logging.getLogger(__name__)
SENTINEL = object()


class Background:
    def __init__(
        self,
        *,
        loop=None,
        q=None,
        concurrency=10,
        waittime=0.1,
        return_exceptions=False,
    ):
        if loop is not None:
            self.loop = loop
        self.q = q or asyncio.Queue()
        self.concurrency = concurrency
        self.waittime = waittime
        self.tasks = []
        self.return_exceptions = return_exceptions

    @reify
    def loop(self):
        return get_event_loop()

    def add(self, fn, *args, **kwargs):
        self.q.put_nowait((fn, args, kwargs))

    def __iter__(self):
        q = self.q
        n = self.concurrency
        loop = self.loop
        outq = asyncio.Queue()
        logger.info("background computation, start, concurrency=%d, tasks=%s", n, q.qsize())

        async def consume(i):
            while True:
                val = await q.get()
                if val is SENTINEL:
                    q.task_done()
                    break
                try:
                    fn, args, kwargs = val
                    ret = await run_async_contextually(loop, fn, args, kwargs)
                    outq.put_nowait((ret, None))
                    q.task_done()
                except Exception as e:
                    q.task_done()
                    outq.put_nowait((None, e))

        for i in range(n):
            self.tasks.append(loop.create_task(consume(i)))

        def ping(count):
            logger.debug("background computation(%d) %s", count, q)
            if q.empty() and q._unfinished_tasks == 0 and outq.empty(
            ) and outq._unfinished_tasks == 0:
                logger.info("background computation, finished")
                for i in range(n):
                    q.put_nowait(SENTINEL)
                outq.put_nowait((SENTINEL, None))
            else:
                loop.call_later(self.waittime, ping, count + 1)

        loop.call_later(self.waittime, ping, 0)

        while True:
            val, err = loop.run_until_complete(outq.get())
            if err is not None:
                if self.return_exceptions:
                    yield err
                    outq.task_done()
                else:
                    outq.task_done()
                    raise err
            elif val is SENTINEL:
                outq.task_done()
                return
            else:
                yield val
                outq.task_done()

    def __enter__(self):
        return self

    def __exit__(self, typ, val, tb):
        for task in self.tasks:
            task.cancel()
        self.loop.stop()

