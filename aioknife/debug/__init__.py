import asyncio
import logging
logger = logging.getLogger(__name__)


class Inspector:
    def __init__(self, *, prefix="", _logger=None):
        self.prefix = prefix
        self.logger = _logger

    def format_queue(self, q):
        return format_queue(q)

    def display_queue(self, q):
        self.logger.debug("%s%s", self.prefix, self.format(q))

    def watch_queue(self, loop, q, *, delay=0.5):
        while True:
            self.display_queuelay(q)
            asyncio.sleep(delay, loop=loop)


def format_queue(q):
    return f"q(size={q.qsize()}, unfinished={q._unfinished_tasks})"
