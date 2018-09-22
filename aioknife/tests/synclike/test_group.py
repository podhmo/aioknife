import unittest
import time


class Tests(unittest.TestCase):
    def _makeOne(self, *args, **kwargs):
        from aioknife.synclike import Group
        return Group(*args, **kwargs)

    def test_it__sync(self):
        def run(i):
            time.sleep(0.05)
            return i

        st = time.time()
        target = self._makeOne()
        for i in range(10):
            target.go(run, i)
        got = target.wait()
        expected = list(range(10))
        self.assertEqual(got, expected)

        self.assertGreater(time.time() - st, 0.05)
        self.assertLessEqual(time.time() - st, 0.1)

    def test_it__async(self):
        import asyncio

        async def run(i):
            await asyncio.sleep(0.05)
            return i

        st = time.time()
        target = self._makeOne()
        for i in range(10):
            target.go(run, i)
        got = target.wait()
        expected = list(range(10))
        self.assertEqual(got, expected)

        self.assertGreater(time.time() - st, 0.05)
        self.assertLessEqual(time.time() - st, 0.1)

    def test_it__async__with_limit(self):
        import asyncio

        async def run(i):
            await asyncio.sleep(0.05)
            return i

        st = time.time()
        target = self._makeOne(limit=5)
        for i in range(10):
            target.go(run, i)
        got = target.wait()
        expected = list(range(10))
        self.assertEqual(got, expected)

        self.assertGreaterEqual(time.time() - st, 0.1)
        self.assertLessEqual(time.time() - st, 0.2)
