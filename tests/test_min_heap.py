"""최솟값 추출, 만료 예약의 비교, 반복 연산 중 힙 조건을 검증한다."""

import random
import unittest

from mini_redis.min_heap import MinHeap


class PriorityItem:
    """< 비교만 제공하는 객체로 반환된 항목의 정체성도 확인한다."""

    def __init__(self, priority):
        self.priority = priority

    def __lt__(self, other):
        return self.priority < other.priority


class MinHeapTests(unittest.TestCase):
    def assert_heap(self, heap, expected_size):
        """모든 부모·자식 쌍이 힙 조건을 만족하는지 확인한다."""
        self.assertEqual(heap.size(), expected_size)
        self.assertEqual(len(heap), expected_size)
        for index in range(1, expected_size):
            parent = (index - 1) // 2
            self.assertFalse(heap._items[index] < heap._items[parent])

    def test_empty_heap(self):
        heap = MinHeap()
        self.assertIsNone(heap.peek())
        self.assertIsNone(heap.pop())
        self.assertIsNone(heap.pop())
        self.assert_heap(heap, 0)

    def test_single_item_and_reuse(self):
        heap = MinHeap()
        heap.push((10, "name"))
        self.assertEqual(heap.peek(), (10, "name"))
        self.assertEqual(heap.pop(), (10, "name"))
        self.assert_heap(heap, 0)
        heap.push((5, "new"))
        self.assertEqual(heap.pop(), (5, "new"))
        self.assertIsNone(heap.peek())

    def test_extract_in_order_for_various_insertions(self):
        for values in (
            list(range(40)),
            list(range(40, 0, -1)),
            [9, 3, 7, 1, 8, 2, 6, 4, 5],
            [4, 4, 4, 4],
            [0, -2, 1.5, -0.5, 0, 100],
        ):
            with self.subTest(values=values):
                heap = MinHeap()
                for count, value in enumerate(values, start=1):
                    heap.push(value)
                    self.assert_heap(heap, count)
                for index, expected in enumerate(sorted(values)):
                    self.assertEqual(heap.pop(), expected)
                    self.assert_heap(heap, len(values) - index - 1)
                self.assertIsNone(heap.pop())

    def test_ttl_records_compare_time_then_key(self):
        records = [(30.5, "later"), (10, "나"), (10, "가"), (20, "middle"), (10, "가")]
        heap = MinHeap()
        for record in records:
            heap.push(record)
        self.assertEqual([heap.pop() for _ in records], sorted(records))
        self.assert_heap(heap, 0)

    def test_reservation_numbers_can_break_remaining_ties(self):
        records = [(10, "key", 3), (10, "key", 1), (5, "other", 2)]
        heap = MinHeap()
        for record in records:
            heap.push(record)
        self.assertEqual([heap.pop() for _ in records], sorted(records))

    def test_peek_does_not_remove_or_reorder_items(self):
        heap = MinHeap()
        for value in (4, 1, 3, 2):
            heap.push(value)
        before = heap._items[:]
        for _ in range(5):
            self.assertEqual(heap.peek(), 1)
        self.assertEqual(heap._items, before)
        self.assert_heap(heap, 4)

    def test_pop_with_only_left_child(self):
        heap = MinHeap()
        for value in (1, 2, 3):
            heap.push(value)
        self.assertEqual(heap.pop(), 1)
        self.assertEqual(heap.peek(), 2)
        self.assert_heap(heap, 2)
        self.assertEqual(heap.pop(), 2)
        self.assertEqual(heap.pop(), 3)

    def test_pop_selects_smaller_right_child(self):
        heap = MinHeap()
        for value in (1, 4, 2, 5, 6, 3):
            heap.push(value)
        self.assertEqual(heap.pop(), 1)
        self.assertEqual(heap.peek(), 2)
        self.assert_heap(heap, 5)
        self.assertEqual([heap.pop() for _ in range(5)], [2, 3, 4, 5, 6])

    def test_interleaved_push_and_pop(self):
        heap = MinHeap()
        expected = []
        generator = random.Random(42)
        for _ in range(300):
            if not expected or generator.random() < 0.6:
                item = (generator.randrange(20), "key" + str(generator.randrange(10)))
                heap.push(item)
                expected.append(item)
                expected.sort()
            else:
                self.assertEqual(heap.pop(), expected.pop(0))
            self.assert_heap(heap, len(expected))
            self.assertEqual(heap.peek(), expected[0] if expected else None)
        self.assertEqual([heap.pop() for _ in expected], expected)
        self.assert_heap(heap, 0)

    def test_less_than_comparison_preserves_object_identity(self):
        heap = MinHeap()
        first = PriorityItem(1)
        second = PriorityItem(2)
        third = PriorityItem(3)
        for item in (third, first, second):
            heap.push(item)
        self.assertIs(heap.peek(), first)
        self.assertIs(heap.pop(), first)
        self.assertIs(heap.pop(), second)
        self.assertIs(heap.pop(), third)


if __name__ == "__main__":
    unittest.main()
