import asyncio
import contextlib
from .langhelpers import (
    reify,
    get_event_loop,
    run_async_contextually,
)


class _LazyAsyncContextManager:
    def __init__(self, fn):
        self.fn = fn
        self.actx = None

    def __getattr__(self, name):
        return _LazyMethod(self, name)

    def _bind(self, actx):
        self.actx = actx


class _LazyMethod:
    def __init__(self, manager, name):
        self.manager = manager
        self.name = name

    def __call__(self, *args, **kwargs):
        fn = getattr(self.manager.actx, self.name)
        return fn(*args, **kwargs)

    def __repr__(self):
        return f"<Lazy {self.manager.actx!r}, {self.name!r}>"


class Group:
    def __init__(self, *, loop=None, limit=None, middleware=None):
        self.tasks = []

        if loop is not None:
            self.loop = loop

        self.middleware = middleware or []
        if limit is not None:
            self.middleware.append(asyncio.Semaphore(limit))

    @reify
    def loop(self):
        return get_event_loop()

    def go(self, fn, *args, **kwargs):
        return self.tasks.append(("task", fn, args, kwargs))

    def wait(self):
        coro = self.coroutinefunction()
        return self.loop.run_until_complete(coro)

    @contextlib.contextmanager
    def __call__(self, fn, *args, **kwargs):
        lazy_actx = _LazyAsyncContextManager(fn)
        self.tasks.append(("actx", lazy_actx, args, kwargs))
        yield lazy_actx

    async def coroutinefunction(self, *, loop=None):
        tasks = []
        loop = loop or self.loop
        async with contextlib.AsyncExitStack() as s:
            for kind, lazy_actx, args, kwargs in self.tasks:
                if kind == "actx":
                    actx = lazy_actx.fn(*args, **kwargs)
                    await s.enter_async_context(actx)
                    lazy_actx._bind(actx)

            for kind, fn, args, kwargs in self.tasks:
                if kind == "task":
                    tasks.append(self._create_task(fn, args, kwargs))
            return await asyncio.gather(*tasks, loop=loop)

    async def _create_task(self, fn, args, kwargs):
        async with contextlib.AsyncExitStack() as s:
            for actx in self.middleware:
                await s.enter_async_context(actx)
            return await run_async_contextually(self.loop, fn, args, kwargs)
