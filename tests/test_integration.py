"""명령을 조합한 뒤 자료구조와 메모리·TTL 상태의 일관성을 검증한다."""

import unittest
from unittest.mock import patch

from mini_redis.cli import execute_command
from mini_redis.store import RedisStore
from tests.helpers import ManualClock


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.clock = ManualClock()
        clock_patch = patch("mini_redis.store.time.monotonic", self.clock)
        clock_patch.start()
        self.addCleanup(clock_patch.stop)
        self.store = RedisStore()

    def assert_state(self, expected, limit, evicted):
        """추가 명령을 실행하지 않고 키·값·LRU·TTL·사용량을 함께 확인한다."""
        store = self.store
        self.assertEqual(store._data.size(), len(expected))
        self.assertEqual(len(store._lru), len(expected))
        self.assertEqual(
            sorted(store._data.keys()), sorted(key for key, _, _ in expected)
        )
        used = sum(
            len(key.encode("utf-8")) + len(value.encode("utf-8"))
            for key, value, _ in expected
        )
        self.assertEqual(store._used_memory, used)
        self.assertEqual(store._maxmemory, limit)
        self.assertEqual(store._evicted_keys, evicted)

        node = store._lru.head
        previous = None
        for key, value, deadline in expected:
            self.assertIsNotNone(node)
            self.assertEqual(node.data, key)
            self.assertIs(node.prev, previous)
            self.assertIs(node._owner, store._lru)
            entry = store._data.get(key)
            self.assertEqual(entry.value, value)
            self.assertEqual(entry.expire_at, deadline)
            self.assertIs(entry.lru_node, node)
            self.assertEqual(
                entry.memory_size,
                len(key.encode("utf-8")) + len(value.encode("utf-8")),
            )
            if deadline is None:
                self.assertIsNone(entry.expiry_id)
            else:
                self.assertGreater(deadline, self.clock.now)
                self.assertIn(
                    (deadline, key, entry.expiry_id), store._expiry_heap._items
                )
            previous = node
            node = node.next
        self.assertIsNone(node)
        self.assertIs(store._lru.tail, previous)

        following = None
        node = store._lru.tail
        for key, _, _ in reversed(expected):
            self.assertIsNotNone(node)
            self.assertEqual(node.data, key)
            self.assertIs(node.next, following)
            following = node
            node = node.prev
        self.assertIsNone(node)
        self.assertIs(store._lru.head, following)

    def test_complete_command_lifecycle(self):
        def step(command, result, state, limit=8, evicted=0):
            with self.subTest(command=command):
                self.assertEqual(execute_command(command, self.store), result)
                self.assert_state(state, limit, evicted)

        step("CONFIG SET maxmemory 8", "OK", [])
        step("SET a 1", "OK", [("a", "1", None)])
        step("SET b 2", "OK", [("b", "2", None), ("a", "1", None)])
        step("EXPIRE a 2", "(integer) 1", [("b", "2", None), ("a", "1", 102)])
        step("EXPIRE a 10", "(integer) 1", [("b", "2", None), ("a", "1", 110)])
        step("SET c 3", "OK", [("c", "3", None), ("b", "2", None), ("a", "1", 110)])
        step("GET a", '"1"', [("a", "1", 110), ("c", "3", None), ("b", "2", None)])
        four = [("d", "4", None), ("a", "1", 110), ("c", "3", None), ("b", "2", None)]
        step("SET d 4", "OK", four)
        self.clock.advance(2)
        step("TTL a", "(integer) 8", four)
        step("SET e 5", "OK", [("e", "5", None), ("d", "4", None), ("a", "1", 110), ("c", "3", None)], evicted=1)
        step("EXPIRE d 1", "(integer) 1", [("e", "5", None), ("d", "4", 103), ("a", "1", 110), ("c", "3", None)], evicted=1)
        self.clock.advance(1)
        step("SET f 6", "OK", [("f", "6", None), ("e", "5", None), ("a", "1", 110), ("c", "3", None)], evicted=1)
        three = [("a", "XXX", None), ("f", "6", None), ("e", "5", None)]
        step("SET a XXX", "OK", three, evicted=2)
        step("EXPIRE a abc", "(error) ERR value is not an integer or out of range", three, evicted=2)
        step("SET a 0123456789", "(error) OOM command not allowed when used_memory > 'maxmemory'", three, evicted=2)
        step("EXISTS d", "(integer) 0", three, evicted=2)
        step("EXPIRE e 0", "(integer) 1", three[:2], evicted=2)
        only_a = [("a", "XXX", None)]
        step("DEL f", "(integer) 1", only_a, evicted=2)
        step("CONFIG SET maxmemory 4", "OK", only_a, limit=4, evicted=2)
        self.clock.advance(7)
        step("GET a", '"XXX"', only_a, limit=4, evicted=2)
        step("TTL a", "(integer) -1", only_a, limit=4, evicted=2)
        step("KEYS", '1. "a"', only_a, limit=4, evicted=2)
        step("DBSIZE", "(integer) 1", only_a, limit=4, evicted=2)
        step("DEL a", "(integer) 1", [], limit=4, evicted=2)
        step("DEL a", "(integer) 0", [], limit=4, evicted=2)
        step("INFO memory", "used_memory:0\nmaxmemory:4\nevicted_keys:2", [], limit=4, evicted=2)

    def test_resizing_expiration_overwrite_and_eviction_in_one_batch(self):
        for index in range(60):
            key = "k{:02d}".format(index)
            self.store.set(key, "가")
            self.store.expire(key, 2 if index % 2 == 0 else 4)
        for index in range(0, 60, 4):
            self.store.expire("k{:02d}".format(index), 8)
        for index in range(0, 60, 5):
            self.store.set("k{:02d}".format(index), "나")
        for index in range(0, 60, 7):
            self.store.delete("k{:02d}".format(index))

        # 삽입 순서와 덮어쓴 순서에서 예상 생존 항목을 따로 계산한다.
        expected = []
        order = list(reversed(range(0, 60, 5)))
        order += [index for index in reversed(range(60)) if index % 5 != 0]
        for index in order:
            if index % 7 == 0:
                continue
            value = "나" if index % 5 == 0 else "가"
            deadline = None if index % 5 == 0 else (108 if index % 4 == 0 else (102 if index % 2 == 0 else 104))
            expected.append(("k{:02d}".format(index), value, deadline))
        self.assert_state(expected, 0, 0)

        self.clock.advance(2)
        surviving = [row for row in expected if row[2] is None or row[2] > 102]
        self.assertEqual(self.store.dbsize(), len(surviving))
        self.assert_state(surviving, 0, 0)
        self.store.config_set_maxmemory(36)
        self.assert_state(surviving, 36, 0)
        self.store.set("new", "나")
        kept = [("new", "나", None)] + surviving[:5]
        evicted = len(surviving) + 1 - len(kept)
        self.assert_state(kept, 36, evicted)
        self.clock.advance(10)
        self.assertEqual(sorted(self.store.keys()), sorted(key for key, _, _ in kept))
        self.assert_state(kept, 36, evicted)
        self.assertEqual(self.store._expiry_heap.size(), 0)


if __name__ == "__main__":
    unittest.main()
