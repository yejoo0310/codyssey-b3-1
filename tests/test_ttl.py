"""TTL 재설정과 만료 시점, LRU·메모리 관리와의 조합을 검증한다."""

import unittest

from mini_redis.store import OutOfMemoryError, RedisStore
from tests.helpers import ManualClock


class TTLTests(unittest.TestCase):
    def setUp(self):
        self.clock = ManualClock()
        self.store = RedisStore(clock=self.clock)

    def test_missing_and_persistent_keys(self):
        self.assertEqual(self.store.ttl("missing"), -2)
        self.assertEqual(self.store.expire("missing", 3), 0)
        self.assertEqual(self.store._expiry_heap.size(), 0)
        self.store.set("a", "1")
        self.assertEqual(self.store.ttl("a"), -1)

    def test_fractional_remaining_time_and_exact_deadline(self):
        self.store.set("a", "1")
        self.assertEqual(self.store.expire("a", 3), 1)
        self.assertEqual(self.store.ttl("a"), 3)
        self.clock.advance(0.25)
        self.assertEqual(self.store.ttl("a"), 2)
        self.clock.advance(2)
        self.assertEqual(self.store.ttl("a"), 0)
        self.assertEqual(self.store.get("a"), "1")
        self.clock.advance(0.75)
        self.assertEqual(self.store.ttl("a"), -2)
        self.assertIsNone(self.store.get("a"))
        self.assertEqual(self.store.info_memory(), (0, 0, 0))

    def test_nonpositive_seconds_delete_immediately(self):
        for seconds in (0, -1, -100):
            with self.subTest(seconds=seconds):
                self.store.set("a", "1")
                self.assertEqual(self.store.expire("a", seconds), 1)
                self.assertEqual(self.store.expire("a", seconds), 0)
                self.assertEqual(self.store.ttl("a"), -2)
                self.assertEqual(len(self.store._lru), 0)
                self.assertEqual(self.store.info_memory(), (0, 0, 0))

    def test_key_commands_treat_expired_key_as_missing(self):
        for command, expected in (("get", None), ("exists", 0), ("delete", 0), ("ttl", -2), ("expire", 0)):
            with self.subTest(command=command):
                clock = ManualClock()
                store = RedisStore(clock=clock)
                store.set("a", "1")
                store.expire("a", 1)
                clock.advance(1)
                method = getattr(store, command)
                result = method("a", 10) if command == "expire" else method("a")
                self.assertEqual(result, expected)
                self.assertEqual(store.info_memory(), (0, 0, 0))
                self.assertEqual(len(store._lru), 0)

    def test_global_queries_clean_unaccessed_expired_keys(self):
        for command in ("dbsize", "keys", "info_memory"):
            with self.subTest(command=command):
                clock = ManualClock()
                store = RedisStore(clock=clock)
                store.set("a", "1")
                store.set("b", "2")
                store.expire("a", 1)
                clock.advance(1)
                result = getattr(store, command)()
                expected = 1 if command == "dbsize" else ["b"]
                if command == "info_memory":
                    expected = (2, 0, 0)
                self.assertEqual(result, expected)
                self.assertEqual(len(store._lru), 1)

    def test_expired_get_does_not_refresh_lru(self):
        self.store.set("a", "1")
        self.store.set("b", "2")
        self.store.expire("a", 1)
        self.clock.advance(1)
        self.assertIsNone(self.store.get("a"))
        self.assertEqual(self.store._lru.head.data, "b")
        self.assertIs(self.store._lru.head, self.store._lru.tail)
        self.assertEqual(self.store.info_memory(), (2, 0, 0))

    def test_set_clears_ttl_and_stale_reservation(self):
        self.store.set("a", "old")
        self.store.expire("a", 2)
        self.store.set("a", "new")
        self.assertEqual(self.store.ttl("a"), -1)
        self.clock.advance(2)
        self.assertEqual(self.store.get("a"), "new")
        self.assertEqual(self.store.ttl("a"), -1)
        self.assertEqual(self.store._expiry_heap.size(), 0)

    def test_extend_expiration_ignores_old_reservation(self):
        self.store.set("a", "1")
        self.store.expire("a", 2)
        self.clock.advance(1)
        self.store.expire("a", 10)
        self.clock.advance(1)
        self.assertEqual(self.store.ttl("a"), 9)
        self.assertEqual(self.store.get("a"), "1")
        self.clock.advance(9)
        self.assertEqual(self.store.ttl("a"), -2)

    def test_shorten_expiration_removes_at_new_deadline(self):
        self.store.set("a", "old")
        self.store.expire("a", 10)
        self.store.expire("a", 2)
        self.clock.advance(2)
        self.assertIsNone(self.store.get("a"))
        self.store.set("a", "new")
        self.clock.advance(8)
        self.assertEqual(self.store.get("a"), "new")
        self.assertEqual(self.store.info_memory(), (4, 0, 0))

    def test_delete_then_recreate_with_new_expiration(self):
        self.store.set("a", "old")
        self.store.expire("a", 2)
        self.assertEqual(self.store.delete("a"), 1)
        self.store.set("a", "new")
        self.store.expire("a", 10)
        self.clock.advance(2)
        self.assertEqual(self.store.get("a"), "new")
        self.assertEqual(self.store.ttl("a"), 8)
        self.clock.advance(8)
        self.assertIsNone(self.store.get("a"))

    def test_equal_deadlines_remove_each_key_only_once(self):
        for key in ("a", "i", "q"):
            self.store.set(key, "1")
            self.store.expire(key, 2)
            self.store.expire(key, 2)
        self.clock.advance(2)
        self.assertEqual(self.store.dbsize(), 0)
        self.assertEqual(self.store.info_memory(), (0, 0, 0))
        self.assertEqual(self.store._expiry_heap.size(), 0)
        self.assertEqual(len(self.store._lru), 0)

    def test_expire_and_ttl_do_not_refresh_lru(self):
        self.store.config_set_maxmemory(4)
        self.store.set("a", "1")
        self.store.set("b", "2")
        self.store.expire("a", 10)
        self.assertEqual(self.store.ttl("a"), 10)
        self.store.set("c", "3")
        self.assertEqual(self.store.exists("a"), 0)
        self.assertEqual(self.store.info_memory(), (4, 4, 1))

    def test_expiration_frees_memory_before_lru_eviction(self):
        self.store.config_set_maxmemory(4)
        self.store.set("a", "1")
        self.store.set("b", "2")
        self.store.expire("b", 1)
        self.clock.advance(1)
        self.store.set("c", "3")
        self.assertEqual(sorted(self.store.keys()), ["a", "c"])
        self.assertEqual(self.store.info_memory(), (4, 4, 0))

    def test_evicted_key_reservations_do_not_delete_recreated_key(self):
        self.store.config_set_maxmemory(2)
        self.store.set("a", "1")
        self.store.expire("a", 2)
        self.store.set("b", "2")
        self.store.set("a", "3")
        self.store.expire("a", 10)
        self.clock.advance(2)
        self.assertEqual(self.store.get("a"), "3")
        self.assertEqual(self.store.ttl("a"), 8)
        self.assertEqual(self.store.info_memory(), (2, 2, 2))

    def test_oom_preserves_live_ttl_and_lru(self):
        self.store.config_set_maxmemory(4)
        self.store.set("a", "1")
        self.store.set("b", "2")
        self.store.expire("a", 10)
        with self.assertRaises(OutOfMemoryError):
            self.store.set("a", "too long")
        self.assertEqual(self.store.ttl("a"), 10)
        self.assertEqual(self.store._lru.head.data, "b")
        self.assertEqual(self.store.info_memory(), (4, 4, 0))

    def test_oom_can_clean_expired_keys_without_eviction(self):
        self.store.config_set_maxmemory(4)
        self.store.set("a", "1")
        self.store.set("b", "2")
        self.store.expire("b", 1)
        self.clock.advance(1)
        with self.assertRaises(OutOfMemoryError):
            self.store.set("a", "too long")
        self.assertEqual(self.store.info_memory(), (2, 4, 0))
        self.assertEqual(self.store.get("a"), "1")

    def test_set_after_expiration_creates_fresh_entry(self):
        self.store.set("a", "old")
        self.store.expire("a", 1)
        self.clock.advance(1)
        self.store.set("a", "new value")
        self.assertEqual(self.store.ttl("a"), -1)
        self.assertEqual(self.store.get("a"), "new value")
        self.assertEqual(self.store.info_memory(), (10, 0, 0))
        self.assertEqual(len(self.store._lru), 1)

    def test_invalid_seconds_preserve_existing_deadline(self):
        self.store.set("a", "1")
        self.store.expire("a", 5)
        for invalid in (None, True, 1.5, "3", 10 ** 400):
            with self.subTest(seconds=invalid):
                with self.assertRaises(ValueError):
                    self.store.expire("a", invalid)
                self.assertEqual(self.store.ttl("a"), 5)
        for method in (self.store.expire, self.store.ttl):
            with self.assertRaises(TypeError):
                method(None, 3) if method.__name__ == "expire" else method(None)

    def test_empty_key_and_empty_value_can_expire(self):
        self.store.set("", "")
        self.assertEqual(self.store.expire("", 1), 1)
        self.clock.advance(1)
        self.assertEqual(self.store.ttl(""), -2)
        self.assertEqual(len(self.store._lru), 0)
        self.assertEqual(self.store.info_memory(), (0, 0, 0))

    def test_batch_expiration_after_hash_map_resizing(self):
        for index in range(100):
            key = "key" + str(index)
            self.store.set(key, "값")
            self.store.expire(key, index % 5 + 1)
        self.clock.advance(5)
        self.assertEqual(self.store.keys(), [])
        self.assertEqual(self.store.info_memory(), (0, 0, 0))
        self.assertEqual(len(self.store._lru), 0)
        self.assertEqual(self.store._expiry_heap.size(), 0)


if __name__ == "__main__":
    unittest.main()
