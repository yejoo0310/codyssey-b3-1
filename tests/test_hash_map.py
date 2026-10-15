"""해시 충돌, 키 덮어쓰기, 버킷 확장 후의 데이터 보존을 확인한다."""

import unittest

from mini_redis.hash_map import HashMap


class CollidingHashMap(HashMap):
    """모든 키를 한 버킷에 넣어 충돌 상황을 만든다."""

    def _hash(self, key):
        return 0


class HashMapTests(unittest.TestCase):
    def test_empty_map(self):
        mapping = HashMap()
        self.assertEqual(mapping.size(), 0)
        self.assertEqual(len(mapping), 0)
        self.assertEqual(mapping.keys(), [])
        self.assertIsNone(mapping.get("missing"))
        self.assertFalse(mapping.contains("missing"))
        self.assertFalse(mapping.remove("missing"))
        self.assertEqual(mapping.size(), 0)

    def test_put_get_and_contains(self):
        mapping = HashMap()
        mapping.put("name", "Alice")
        mapping.put("age", 20)
        self.assertEqual(mapping.get("name"), "Alice")
        self.assertEqual(mapping.get("age"), 20)
        self.assertTrue(mapping.contains("name"))
        self.assertFalse(mapping.contains("other"))
        self.assertEqual(mapping.size(), 2)
        self.assertEqual(sorted(mapping.keys()), ["age", "name"])

    def test_overwrite_does_not_grow_or_resize(self):
        mapping = HashMap(initial_capacity=4)
        for key in ("a", "b", "c"):
            mapping.put(key, "old")
        mapping.put("b", "new")
        self.assertEqual(mapping.get("b"), "new")
        self.assertEqual(mapping.size(), 3)
        self.assertEqual(mapping.capacity, 4)
        self.assertEqual(sorted(mapping.keys()), ["a", "b", "c"])

    def test_none_value_is_distinct_from_missing_key(self):
        mapping = HashMap()
        mapping.put("nullable", None)
        self.assertIsNone(mapping.get("nullable"))
        self.assertTrue(mapping.contains("nullable"))
        self.assertTrue(mapping.remove("nullable"))
        self.assertFalse(mapping.contains("nullable"))
        self.assertEqual(mapping.size(), 0)

    def test_empty_unicode_and_case_sensitive_keys(self):
        mapping = HashMap()
        keys = ["", "이름", "🔑", "Name", "name", "가" * 1000]
        for value, key in enumerate(keys):
            mapping.put(key, value)
        for value, key in enumerate(keys):
            self.assertEqual(mapping.get(key), value)
        self.assertEqual(sorted(mapping.keys()), sorted(keys))

    def test_natural_collisions_keep_values_separate(self):
        mapping = HashMap(initial_capacity=8)
        # 한 글자 키 a, i, q는 버킷이 8개일 때 같은 위치에 들어간다.
        self.assertEqual(mapping._bucket_index("a"), mapping._bucket_index("i"))
        self.assertEqual(mapping._bucket_index("i"), mapping._bucket_index("q"))
        for key in ("a", "i", "q"):
            mapping.put(key, key.upper())
        mapping.put("i", "updated")
        self.assertEqual(mapping.get("a"), "A")
        self.assertEqual(mapping.get("i"), "updated")
        self.assertEqual(mapping.get("q"), "Q")
        self.assertIsNone(mapping.get("y"))
        self.assertFalse(mapping.remove("y"))
        self.assertEqual(mapping.size(), 3)

    def test_remove_each_position_in_collision_chain(self):
        keys = ["a", "i", "q"]
        for removed_key in keys:
            with self.subTest(key=removed_key):
                mapping = HashMap(initial_capacity=8)
                for key in keys:
                    mapping.put(key, key.upper())
                self.assertTrue(mapping.remove(removed_key))
                self.assertFalse(mapping.remove(removed_key))
                self.assertFalse(mapping.contains(removed_key))
                self.assertIsNone(mapping.get(removed_key))
                remaining = [key for key in keys if key != removed_key]
                self.assertEqual(mapping.size(), 2)
                self.assertEqual(sorted(mapping.keys()), sorted(remaining))
                for key in remaining:
                    self.assertEqual(mapping.get(key), key.upper())

    def test_resize_only_above_threshold(self):
        mapping = HashMap(initial_capacity=4)
        for key in ("a", "e", "i"):
            mapping.put(key, key)
        self.assertEqual(mapping.capacity, 4)
        mapping.put("m", "m")
        self.assertEqual(mapping.capacity, 8)
        self.assertEqual(mapping.size(), 4)
        for key in ("a", "e", "i", "m"):
            self.assertEqual(mapping.get(key), key)

    def test_repeated_resizing_preserves_value_objects(self):
        mapping = HashMap(initial_capacity=1)
        values = [object() for _ in range(100)]
        for index, value in enumerate(values):
            old_capacity = mapping.capacity
            mapping.put(str(index), value)
            expected_capacity = old_capacity
            if mapping.size() * 4 > old_capacity * 3:
                expected_capacity *= 2
            self.assertEqual(mapping.capacity, expected_capacity)
            self.assertLessEqual(mapping.size() / mapping.capacity, 0.75)
        self.assertEqual(mapping.size(), len(values))
        self.assertEqual(sorted(mapping.keys()), sorted(str(i) for i in range(100)))
        for index, value in enumerate(values):
            self.assertIs(mapping.get(str(index)), value)

    def test_collisions_survive_resizing_and_deletion(self):
        mapping = CollidingHashMap(initial_capacity=2)
        for index in range(40):
            mapping.put(str(index), index)
        for index in range(0, 40, 2):
            self.assertTrue(mapping.remove(str(index)))
        for index in range(40):
            if index % 2 == 0:
                self.assertFalse(mapping.contains(str(index)))
            else:
                self.assertEqual(mapping.get(str(index)), index)
        expected = [str(index) for index in range(1, 40, 2)]
        self.assertEqual(sorted(mapping.keys()), sorted(expected))
        self.assertEqual(mapping.size(), 20)

    def test_delete_all_and_reinsert(self):
        mapping = HashMap(initial_capacity=2)
        for index in range(20):
            mapping.put(str(index), index)
        for index in range(20):
            self.assertTrue(mapping.remove(str(index)))
        self.assertEqual(mapping.size(), 0)
        self.assertEqual(mapping.keys(), [])
        mapping.put("new", "value")
        self.assertEqual(mapping.get("new"), "value")
        self.assertEqual(mapping.size(), 1)

    def test_keys_returns_independent_array(self):
        mapping = HashMap()
        mapping.put("original", "value")
        keys = mapping.keys()
        keys[0] = "changed"
        self.assertEqual(mapping.keys(), ["original"])
        self.assertEqual(mapping.get("original"), "value")

    def test_invalid_capacity(self):
        for capacity in (0, -1, 1.5, "8", None, True):
            with self.subTest(capacity=capacity):
                with self.assertRaises(ValueError):
                    HashMap(initial_capacity=capacity)

    def test_reject_non_string_keys_without_changes(self):
        mapping = HashMap()
        mapping.put("kept", "value")
        for invalid in (None, 1, True):
            for method in (mapping.get, mapping.contains, mapping.remove, mapping.put):
                with self.subTest(key=invalid, method=method.__name__):
                    with self.assertRaises(TypeError):
                        if method.__name__ == "put":
                            method(invalid, "new")
                        else:
                            method(invalid)
                    self.assertEqual(mapping.size(), 1)
                    self.assertEqual(mapping.get("kept"), "value")


if __name__ == "__main__":
    unittest.main()
