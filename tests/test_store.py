"""기본 명령을 조합했을 때 값과 키 개수가 일관되게 유지되는지 확인한다."""

import unittest

from mini_redis.store import RedisStore


class RedisStoreTests(unittest.TestCase):
    def test_empty_store(self):
        store = RedisStore()
        self.assertIsNone(store.get("missing"))
        self.assertEqual(store.exists("missing"), 0)
        self.assertEqual(store.delete("missing"), 0)
        self.assertEqual(store.dbsize(), 0)
        self.assertEqual(store.keys(), [])

    def test_save_and_read_multiple_strings(self):
        store = RedisStore()
        self.assertEqual(store.set("name", "Alice"), "OK")
        self.assertEqual(store.set("age", "20"), "OK")
        self.assertEqual(store.get("name"), "Alice")
        self.assertEqual(store.get("age"), "20")
        self.assertEqual(store.exists("name"), 1)
        self.assertEqual(store.dbsize(), 2)
        self.assertEqual(sorted(store.keys()), ["age", "name"])

    def test_overwrite_keeps_one_key(self):
        store = RedisStore()
        store.set("name", "Alice")
        self.assertEqual(store.set("name", "Bob"), "OK")
        self.assertEqual(store.get("name"), "Bob")
        self.assertEqual(store.exists("name"), 1)
        self.assertEqual(store.dbsize(), 1)
        self.assertEqual(store.keys(), ["name"])

    def test_missing_key_does_not_change_existing_data(self):
        store = RedisStore()
        store.set("kept", "value")
        self.assertIsNone(store.get("missing"))
        self.assertEqual(store.exists("missing"), 0)
        self.assertEqual(store.delete("missing"), 0)
        self.assertEqual(store.get("kept"), "value")
        self.assertEqual(store.dbsize(), 1)
        self.assertEqual(store.keys(), ["kept"])

    def test_empty_key_and_value_are_valid_strings(self):
        store = RedisStore()
        store.set("", "")
        self.assertEqual(store.get(""), "")
        self.assertEqual(store.exists(""), 1)
        self.assertEqual(store.dbsize(), 1)
        self.assertEqual(store.keys(), [""])
        self.assertEqual(store.delete(""), 1)
        self.assertIsNone(store.get(""))
        self.assertEqual(store.exists(""), 0)
        self.assertEqual(store.dbsize(), 0)

    def test_preserve_unicode_spaces_quotes_and_case(self):
        store = RedisStore()
        pairs = [
            ("이름", "김예주"),
            ("🔑", "값 🔒"),
            ("Name", "Alice Kim"),
            ("name", 'say "hello"'),
            ("001", "000123"),
        ]
        for key, value in pairs:
            store.set(key, value)
        for key, value in pairs:
            self.assertEqual(store.get(key), value)
        self.assertEqual(store.dbsize(), len(pairs))
        self.assertEqual(sorted(store.keys()), sorted(key for key, _ in pairs))

    def test_delete_each_position_in_collision_chain(self):
        # a, i, q는 기본 버킷 수 8에서 같은 위치에 저장된다.
        keys = ["a", "i", "q"]
        for removed_key in keys:
            with self.subTest(key=removed_key):
                store = RedisStore()
                for key in keys:
                    store.set(key, key.upper())
                self.assertEqual(store.delete(removed_key), 1)
                self.assertEqual(store.delete(removed_key), 0)
                self.assertEqual(store.exists(removed_key), 0)
                self.assertIsNone(store.get(removed_key))
                remaining = [key for key in keys if key != removed_key]
                self.assertEqual(store.dbsize(), 2)
                self.assertEqual(sorted(store.keys()), sorted(remaining))
                for key in remaining:
                    self.assertEqual(store.get(key), key.upper())

    def test_mixed_commands_after_hash_map_resizing(self):
        store = RedisStore()
        for index in range(100):
            store.set(str(index), "original")
        for index in range(0, 100, 3):
            self.assertEqual(store.delete(str(index)), 1)
        remaining = [str(index) for index in range(100) if index % 3 != 0]
        for key in remaining:
            store.set(key, "updated:" + key)
        self.assertEqual(store.dbsize(), len(remaining))
        self.assertEqual(sorted(store.keys()), sorted(remaining))
        for index in range(100):
            key = str(index)
            if index % 3 == 0:
                self.assertIsNone(store.get(key))
                self.assertEqual(store.exists(key), 0)
            else:
                self.assertEqual(store.get(key), "updated:" + key)
                self.assertEqual(store.exists(key), 1)

    def test_keys_are_a_snapshot(self):
        store = RedisStore()
        store.set("first", "A")
        snapshot = store.keys()
        store.set("second", "B")
        self.assertEqual(snapshot, ["first"])
        snapshot[0] = "changed"
        self.assertEqual(sorted(store.keys()), ["first", "second"])
        self.assertEqual(store.get("first"), "A")

    def test_stores_do_not_share_data(self):
        first = RedisStore()
        second = RedisStore()
        first.set("name", "Alice")
        second.set("name", "Bob")
        first.delete("name")
        self.assertEqual(first.dbsize(), 0)
        self.assertEqual(second.get("name"), "Bob")
        self.assertEqual(second.dbsize(), 1)

    def test_reject_non_string_keys_without_changes(self):
        store = RedisStore()
        store.set("kept", "value")
        for invalid in (None, 1, True, []):
            for method in (store.set, store.get, store.delete, store.exists):
                with self.subTest(key=invalid, method=method.__name__):
                    with self.assertRaises(TypeError):
                        if method.__name__ == "set":
                            method(invalid, "new")
                        else:
                            method(invalid)
                    self.assertEqual(store.get("kept"), "value")
                    self.assertEqual(store.dbsize(), 1)
                    self.assertEqual(store.keys(), ["kept"])

    def test_reject_non_string_values_without_changes(self):
        store = RedisStore()
        store.set("kept", "value")
        for invalid in (None, 1, True, []):
            for key in ("kept", "new"):
                with self.subTest(key=key, value=invalid):
                    with self.assertRaises(TypeError):
                        store.set(key, invalid)
                    self.assertEqual(store.get("kept"), "value")
                    self.assertEqual(store.dbsize(), 1)
                    self.assertEqual(store.keys(), ["kept"])

    def test_delete_all_and_recreate_key(self):
        store = RedisStore()
        store.set("name", "Alice")
        self.assertEqual(store.delete("name"), 1)
        self.assertEqual(store.dbsize(), 0)
        self.assertEqual(store.keys(), [])
        self.assertEqual(store.set("name", "Bob"), "OK")
        self.assertEqual(store.get("name"), "Bob")
        self.assertEqual(store.dbsize(), 1)


if __name__ == "__main__":
    unittest.main()
