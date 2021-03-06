import typing as t
import logging
import asyncio
from aioknife.aq import AQ
from aioknife.debug import Inspector

logger = logging.getLogger(__name__)


class Executor:
    def __init__(
        self,
        *,
        loop: asyncio.BaseEventLoop = None,
        q: asyncio.Queue = None,
        concurrency: int = 10,
        debug: bool = False,
        callback: t.Callable[[asyncio.Future], None] = None,
    ) -> None:
        self._loop = loop or asyncio.get_event_loop()
        self._q = q or asyncio.Queue()
        self._callback = callback

        self.debug = debug
        self.concurrency = concurrency

        self.inspector = Inspector()
        self.aq = AQ(self._loop, q=self._q)
        self.futs = []

    def register(self, afn, *args, **kwargs) -> asyncio.Future:
        fut = self.aq.add(afn, args=args, kwargs=kwargs)
        self.futs.append(fut)
        if self._callback is not None:
            fut.add_done_callback(self._callback)
        return fut

    def __enter__(self):
        return self.register

    def __exit__(self, a, b, c):
        self._loop.run_until_complete(self._execute())
        for fut in self.futs:
            fut.result()

    async def execute(self, *, return_exceptions=False):
        await self._execute()

        if not return_exceptions:
            return [fut.result() for fut in self.futs]

        r = []
        for fut in self.futs:
            exc = fut.exception()
            if exc is None:
                r.append(fut.result())
            else:
                r.append(exc)
        return r

    async def _execute(self):
        n = self.concurrency
        aq = self.aq
        q = aq.q
        loop = self._loop
        inspector = self.inspector

        teardown = lambda: None  # noqa
        if self.debug:
            w = self.loop.create_task(inspector.watch_queue(loop, q))
            teardown = w.cancel

        logger.info("start	concurrency:%d	queue:%s", n, inspector.format_queue(q))
        aq.start(n)
        try:
            await aq.run()
        finally:
            teardown()
        logger.info("end	concurrency:%d	queue:%s", n, inspector.format_queue(q))
