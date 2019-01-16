import asyncio
import logging
from aioknife.debug import format_queue
logger = logging.getLogger(__name__)


class IDGen:
    def __init__(self):
        self.i = 0

    def __call__(self):
        self.i += 1
        return self.i


class AQ:
    """convinient queue"""

    # todo: keyboard interrupt
    # todo: graceful shutdown
    # todo: inspector and if debug option is true, show signature of function

    def __init__(
        self,
        loop: asyncio.BaseEventLoop,
        *,
        q: asyncio.Queue = None,
        idgen=None,
    ):
        self.loop = loop
        self.q = q or asyncio.Queue()
        self._workers = []
        self._idgen = idgen or IDGen()
        self._conts = {}
        self._started = False

    async def _worker(self, k):
        while True:

            i = None
            action = None
            try:
                i, afn, args, kwargs = await self.q.get()
                logger.debug("queue.get[%r]	worker:%r	 afn:%r", i, k, getattr(afn, "__name__", afn))
                result = await afn(*args, **kwargs)
                if callable(result):
                    action = "continue"
                    logger.debug(
                        "task.continue[%r]	worker:%r	afn:%r, cont:%r",
                        i,
                        k,
                        getattr(afn, "__name__", afn),
                        getattr(result, "__name__", result),
                    )
                    self.add(result, args=(), kwargs={}, _id=i)  # await?
                else:
                    action = "result"
                    logger.debug("task.result[%r]	worker:%r", i, k)
                    self._conts.pop(i).set_result(result)
            except asyncio.CancelledError as e:
                action = "cancel"
                logger.debug("task.canceled[%r]	worker:%r	exception:%r", i, k, e)
                # xxx
                for w in self.q._getters:
                    w.cancel()

            except Exception as e:
                action = "error"
                logger.error("task.error[%r]	worker:%r	exception:%r", i, k, e, exc_info=True)
                if i is not None:
                    self._conts.pop(i).set_exception(e)
            finally:
                if action is None:
                    logger.error(
                        "unexpected-action[%r]	worker:%r	action:%r", i, k, action, exc_info=True
                    )
                    raise RuntimeError("action must not be None")

                if (self.q.empty() and action == "cancel"):
                    return
                else:
                    fmt = "queue.done[%r]	worker:%r	action:%r	 %s"
                    logger.debug(fmt, i, k, action, format_queue(self.q))
                    self.q.task_done()

    def add(self, afn, *, args, kwargs, _id=None):
        if not asyncio.iscoroutinefunction(afn):
            raise ValueError(f"{afn!r} is not awaitable function")

        i = _id or self._idgen()
        logger.debug("queue.put[%r]	afn:%r", i, getattr(afn, "__name__", afn))
        self.q.put_nowait((i, afn, args, kwargs))

        fut = self._conts.get(i)
        if fut is None:
            fut = self._conts[i] = self.loop.create_future()
        return fut

    def start(self, n, *, worker=None, max_workers=None):
        self._started = True
        n = max_workers or min(self.q.qsize(), n)
        logger.debug("worker.start	workers:%d", n)

        for k in range(n):
            t = worker or self._worker(k)
            self._workers.append(self.loop.create_task(t))

    def join(self):  # todo: timeout, todo: stop
        return self.loop.run_until_complete(self.run())

    async def run(self):
        if not self._started:
            raise RuntimeError("start() is not called, please calling this method, before join()")

        await self.q.join()
        logger.debug("worker.finished	workers:%d", len(self._workers))
        for k, w in enumerate(self._workers):
            w.cancel()
        assert self.q._unfinished_tasks == 0 and self.q.qsize() == 0
