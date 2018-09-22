import asyncio
from functools import partial
from asyncio import get_event_loop  # noqa


def run_async_contextually(loop, fn, args, kwargs):
    if asyncio.iscoroutinefunction(fn):
        return fn(*args, **kwargs)
    else:
        fn = partial(fn, *args, **kwargs)
        return loop.run_in_executor(None, fn)


class reify(object):
    """cached property"""

    def __init__(self, wrapped):
        self.wrapped = wrapped
        try:
            self.__doc__ = wrapped.__doc__
        except Exception:
            pass

    def __get__(self, inst, objtype=None):
        if inst is None:
            return self
        val = self.wrapped(inst)
        setattr(inst, self.wrapped.__name__, val)
        return val
