"""메모리 계산과 LRU 제거, 실패한 쓰기의 상태 보존을 검증한다."""

import unittest

from mini_redis.store import OutOfMemoryError, RedisStore


class MemoryTests(unittest.TestCase):
    def assert_consistent(self, store, expected_keys, used_memory, evicted_keys):
        """해시맵과 LRU의 키·순서·개수, 메모리 통계를 함께 확인한다."""
        self.assertEqual(sorted(store.keys()), sorted(expected_keys))
        self.assertEqual(store.dbsize(), len(expected_keys))
        self.assertEqual(len(store._lru), len(expected_keys))
        node = store._lru.head
        previous = None
        for key in expected_keys:
            self.assertIsNotNone(node)
            self.assertEqual(node.data, key)
            self.assertIs(node.prev, previous)
            previous = node
            node = node.next
        self.assertIsNone(node)
        self.assertIs(store._lru.tail, previous)
        info = store.info_memory()
        self.assertEqual(info.used_memory, used_memory)
        self.assertEqual(info.evicted_keys, evicted_keys)

    def test_initial_memory_info(self):
        store = RedisStore()
        self.assertEqual(store.info_memory(), (0, 0, 0))

    def test_utf8_size_overwrite_and_delete(self):
        store = RedisStore()
        store.set("가", "🔑")
        self.assert_consistent(store, ["가"], 7, 0)
        store.set("가", "나")
        self.assert_consistent(store, ["가"], 6, 0)
        store.set("a", "")
        self.assert_consistent(store, ["a", "가"], 7, 0)
        self.assertEqual(store.delete("가"), 1)
        self.assertEqual(store.delete("가"), 0)
        self.assert_consistent(store, ["a"], 1, 0)

    def test_requirement_example(self):
        store = RedisStore()
        self.assertEqual(store.config_set_maxmemory(30), "OK")
        for key, value in (("user:1", "Alice"), ("user:2", "Bob"), ("user:3", "Charlie")):
            store.set(key, value)
        self.assertIsNone(store.get("user:1"))
        self.assert_consistent(store, ["user:3", "user:2"], 22, 1)
        self.assertEqual(store.info_memory().maxmemory, 30)

    def test_get_moves_key_to_front(self):
        store = RedisStore()
        store.config_set_maxmemory(4)
        store.set("a", "1")
        store.set("b", "2")
        self.assertEqual(store.get("a"), "1")
        self.assert_consistent(store, ["a", "b"], 4, 0)
        store.set("c", "3")
        self.assert_consistent(store, ["c", "a"], 4, 1)

    def test_overwrite_moves_key_without_duplicate_node(self):
        store = RedisStore()
        store.config_set_maxmemory(4)
        store.set("a", "1")
        store.set("b", "2")
        store.set("a", "X")
        self.assert_consistent(store, ["a", "b"], 4, 0)
        store.set("c", "3")
        self.assert_consistent(store, ["c", "a"], 4, 1)

    def test_only_successful_set_and_get_change_order(self):
        store = RedisStore()
        store.config_set_maxmemory(4)
        store.set("a", "1")
        store.set("b", "2")
        self.assertEqual(store.exists("a"), 1)
        self.assertIsNone(store.get("missing"))
        self.assertEqual(store.delete("missing"), 0)
        store.keys()
        store.dbsize()
        store.info_memory()
        self.assert_consistent(store, ["b", "a"], 4, 0)
        store.set("c", "3")
        self.assert_consistent(store, ["c", "b"], 4, 1)

    def test_new_entry_can_evict_multiple_keys(self):
        store = RedisStore()
        store.config_set_maxmemory(6)
        for key in ("a", "b", "c"):
            store.set(key, "1")
        store.set("d", "12345")
        self.assert_consistent(store, ["d"], 6, 3)

    def test_larger_overwrite_uses_size_difference(self):
        store = RedisStore()
        store.config_set_maxmemory(6)
        for key in ("a", "b", "c"):
            store.set(key, "1")
        store.set("a", "1234")
        self.assert_consistent(store, ["a"], 5, 2)

    def test_smaller_overwrite_releases_memory(self):
        store = RedisStore()
        store.config_set_maxmemory(6)
        store.set("a", "123")
        store.set("b", "1")
        store.set("a", "")
        store.set("c", "12")
        self.assert_consistent(store, ["c", "a", "b"], 6, 0)

    def test_oom_keeps_existing_values_order_and_statistics(self):
        store = RedisStore()
        store.config_set_maxmemory(4)
        store.set("a", "1")
        store.set("b", "2")
        for key in ("a", "new"):
            with self.subTest(key=key):
                with self.assertRaises(OutOfMemoryError):
                    store.set(key, "12345")
                self.assert_consistent(store, ["b", "a"], 4, 0)
        store.set("c", "3")
        self.assert_consistent(store, ["c", "b"], 4, 1)
        self.assertEqual(store.get("b"), "2")

    def test_reduced_limit_is_applied_on_next_successful_set(self):
        store = RedisStore()
        for key in ("a", "b", "c"):
            store.set(key, "1")
        store.config_set_maxmemory(3)
        self.assert_consistent(store, ["c", "b", "a"], 6, 0)
        with self.assertRaises(OutOfMemoryError):
            store.set("d", "123")
        self.assert_consistent(store, ["c", "b", "a"], 6, 0)
        self.assertEqual(store.get("a"), "1")
        store.set("a", "X")
        self.assert_consistent(store, ["a"], 2, 2)

    def test_disabling_limit_keeps_eviction_count(self):
        store = RedisStore()
        store.config_set_maxmemory(2)
        store.set("a", "1")
        store.set("b", "2")
        store.config_set_maxmemory(0)
        store.set("long", "value" * 100)
        self.assert_consistent(store, ["long", "b"], 506, 1)
        self.assertEqual(store.info_memory().maxmemory, 0)

    def test_deleting_keys_never_counts_as_eviction(self):
        store = RedisStore()
        for key in ("a", "i", "q"):
            store.set(key, "1")
        for key, remaining in (("i", ["q", "a"]), ("q", ["a"]), ("a", [])):
            self.assertEqual(store.delete(key), 1)
            self.assert_consistent(store, remaining, len(remaining) * 2, 0)
        store.set("a", "new")
        self.assert_consistent(store, ["a"], 4, 0)

    def test_empty_value_get_updates_lru(self):
        store = RedisStore()
        store.config_set_maxmemory(2)
        store.set("a", "")
        store.set("b", "")
        self.assertEqual(store.get("a"), "")
        store.set("c", "")
        self.assert_consistent(store, ["c", "a"], 2, 1)

    def test_zero_byte_entry_is_removed_when_it_is_oldest(self):
        store = RedisStore()
        store.config_set_maxmemory(2)
        store.set("", "")
        store.set("a", "1")
        store.set("b", "2")
        self.assert_consistent(store, ["b"], 2, 2)

    def test_lru_references_survive_hash_map_resizing(self):
        store = RedisStore()
        keys = ["k{:02d}".format(index) for index in range(40)]
        for key in keys:
            store.set(key, "x")
        store.get(keys[0])
        store.config_set_maxmemory(8)
        store.set(keys[-1], "y")
        self.assert_consistent(store, [keys[-1], keys[0]], 8, 38)

    def test_invalid_limit_keeps_previous_setting(self):
        store = RedisStore()
        store.config_set_maxmemory(10)
        store.set("a", "1")
        for invalid in (-1, 1.5, "10", None, True):
            with self.subTest(limit=invalid):
                with self.assertRaises(ValueError):
                    store.config_set_maxmemory(invalid)
                self.assertEqual(store.info_memory(), (2, 10, 0))

    def test_failed_type_validation_keeps_lru_and_memory(self):
        store = RedisStore()
        store.set("a", "1")
        store.set("b", "2")
        for key, value in (("a", None), (None, "x")):
            with self.subTest(key=key):
                with self.assertRaises(TypeError):
                    store.set(key, value)
                self.assert_consistent(store, ["b", "a"], 4, 0)


if __name__ == "__main__":
    unittest.main()
