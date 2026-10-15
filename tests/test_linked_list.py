"""경계 상황, 양방향 연결, 노드 참조 유지 여부를 검증한다."""

import unittest

from mini_redis.linked_list import DoublyLinkedList, Node


class DoublyLinkedListTests(unittest.TestCase):
    def assert_nodes(self, linked, expected):
        """앞뒤 순회로 순서와 연결을 확인하며 잘못된 순환도 검출한다."""
        self.assertEqual(len(linked), len(expected))
        current = linked.head
        previous = None
        for node in expected:
            self.assertIs(current, node)
            self.assertIs(current.prev, previous)
            previous = current
            current = current.next
        self.assertIsNone(current)
        self.assertIs(linked.tail, previous)

        current = linked.tail
        following = None
        for node in reversed(expected):
            self.assertIs(current, node)
            self.assertIs(current.next, following)
            following = current
            current = current.prev
        self.assertIsNone(current)
        self.assertIs(linked.head, following)

    def test_empty_list(self):
        linked = DoublyLinkedList()
        self.assertIsNone(linked.remove_front())
        self.assertIsNone(linked.remove_back())
        self.assert_nodes(linked, [])

    def test_insert_at_both_ends(self):
        linked = DoublyLinkedList()
        middle = linked.insert_front("middle")
        self.assert_nodes(linked, [middle])
        front = linked.insert_front("front")
        self.assert_nodes(linked, [front, middle])
        back = linked.insert_back("back")
        self.assert_nodes(linked, [front, middle, back])
        self.assertEqual(front.data, "front")
        self.assertEqual(middle.data, "middle")
        self.assertEqual(back.data, "back")

    def test_remove_single_node_and_reuse_empty_list(self):
        for method in ("remove_front", "remove_back", "remove_node"):
            with self.subTest(method=method):
                linked = DoublyLinkedList()
                node = linked.insert_back("only")
                self.assert_nodes(linked, [node])
                if method == "remove_node":
                    removed = linked.remove_node(node)
                else:
                    removed = getattr(linked, method)()
                self.assertIs(removed, node)
                self.assertIsNone(node.prev)
                self.assertIsNone(node.next)
                self.assert_nodes(linked, [])
                replacement = linked.insert_front("new")
                self.assert_nodes(linked, [replacement])

    def test_remove_front_and_back(self):
        linked = DoublyLinkedList()
        first = linked.insert_back(1)
        middle = linked.insert_back(2)
        last = linked.insert_back(3)
        self.assertIs(linked.remove_front(), first)
        self.assert_nodes(linked, [middle, last])
        self.assertIs(linked.remove_back(), last)
        self.assert_nodes(linked, [middle])
        for removed in (first, last):
            self.assertIsNone(removed.prev)
            self.assertIsNone(removed.next)

    def test_remove_node_at_every_position(self):
        for position in range(3):
            with self.subTest(position=position):
                linked = DoublyLinkedList()
                nodes = [linked.insert_back(i) for i in range(3)]
                target = nodes.pop(position)
                self.assertIs(linked.remove_node(target), target)
                self.assert_nodes(linked, nodes)
                self.assertIsNone(target.prev)
                self.assertIsNone(target.next)

    def test_move_to_front_from_every_position(self):
        for count in (1, 2, 3):
            for position in range(count):
                with self.subTest(count=count, position=position):
                    linked = DoublyLinkedList()
                    nodes = [linked.insert_back(i) for i in range(count)]
                    target = nodes.pop(position)
                    linked.move_to_front(target)
                    self.assert_nodes(linked, [target] + nodes)
                    linked.move_to_front(target)
                    self.assert_nodes(linked, [target] + nodes)

    def test_invalid_nodes_do_not_change_either_list(self):
        linked = DoublyLinkedList()
        kept = linked.insert_back("kept")
        removed = linked.insert_back("removed")
        linked.remove_node(removed)
        other = DoublyLinkedList()
        foreign = other.insert_back("foreign")
        for invalid in (Node("unattached"), removed, foreign, None):
            for method in (linked.remove_node, linked.move_to_front):
                with self.subTest(node=invalid, method=method.__name__):
                    with self.assertRaises(ValueError):
                        method(invalid)
                    self.assert_nodes(linked, [kept])
                    self.assert_nodes(other, [foreign])

    def test_reject_node_in_empty_list(self):
        linked = DoublyLinkedList()
        for method in (linked.remove_node, linked.move_to_front):
            with self.subTest(method=method.__name__):
                with self.assertRaises(ValueError):
                    method(Node("unattached"))
                self.assert_nodes(linked, [])

    def test_equal_values_are_distinct_nodes(self):
        linked = DoublyLinkedList()
        first = linked.insert_back("same")
        second = linked.insert_back("same")
        linked.move_to_front(second)
        self.assert_nodes(linked, [second, first])
        linked.remove_node(first)
        self.assert_nodes(linked, [second])

    def test_none_is_valid_data(self):
        linked = DoublyLinkedList()
        node = linked.insert_front(None)
        self.assertIsNone(node.data)
        self.assertIs(linked.remove_front(), node)
        self.assert_nodes(linked, [])

    def test_lru_usage_sequence(self):
        linked = DoublyLinkedList()
        alice = linked.insert_front("alice")
        bob = linked.insert_front("bob")
        charlie = linked.insert_front("charlie")
        linked.move_to_front(alice)
        self.assert_nodes(linked, [alice, charlie, bob])
        self.assertIs(linked.remove_back(), bob)
        self.assert_nodes(linked, [alice, charlie])


if __name__ == "__main__":
    unittest.main()
