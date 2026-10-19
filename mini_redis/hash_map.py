"""같은 버킷의 항목을 이중 연결 리스트로 묶는 해시맵."""

from typing import Any, List, Optional

from mini_redis.linked_list import DoublyLinkedList, Node


class _Entry:
    """키와 값을 하나의 항목으로 보관한다."""

    def __init__(self, key: str, value: Any) -> None:
        self.key = key
        self.value = value


class HashMap:
    """문자열 키를 저장하며, 로드 팩터가 0.75를 넘으면 버킷을 두 배로 늘린다.

    없는 키를 조회하면 None을 반환한다. 값이 None인 키의 존재 여부는
    contains로 확인할 수 있다. keys의 반환 순서는 보장하지 않는다.
    """

    def __init__(self, initial_capacity: int = 8) -> None:
        # 각 버킷은 서로 다른 리스트여야 한다.
        self._buckets = [DoublyLinkedList() for _ in range(initial_capacity)]
        self._size = 0

    def capacity(self) -> int:
        """현재 버킷 개수를 반환한다."""
        return len(self._buckets)

    def size(self) -> int:
        """저장된 키 개수를 반환한다."""
        return self._size

    def _hash(self, key: str) -> int:
        """문자를 차례로 섞어 32비트 범위의 해시값을 만든다."""
        if not isinstance(key, str):
            raise TypeError("key must be a string")
        result = 0
        for character in key:
            # 문자 순서를 반영하고, 계산 중 정수가 계속 커지지 않게 한다.
            result = (result * 31 + ord(character)) & 0xFFFFFFFF
        return result

    def _bucket_index(self, key: str) -> int:
        """해시값을 현재 버킷 범위의 인덱스로 바꾼다."""
        return self._hash(key) % self.capacity()

    def _find_node(self, key: str) -> Optional[Node]:
        """해당 버킷에서 키가 일치하는 노드를 찾는다."""
        node = self._buckets[self._bucket_index(key)].head
        while node is not None:
            if node.data.key == key:
                return node
            node = node.next
        return None

    def put(self, key: str, value: Any) -> None:
        """새 키를 저장하거나 기존 키의 값을 바꾼다."""
        node = self._find_node(key)
        if node is not None:
            node.data.value = value
            return

        bucket = self._buckets[self._bucket_index(key)]
        bucket.insert_back(_Entry(key, value))
        self._size += 1
        # 0.75와 같을 때는 유지하고, 초과할 때만 확장한다.
        if self._size * 4 > self.capacity() * 3:
            self._resize()

    def get(self, key: str) -> Any:
        """키의 값을 반환한다. 없는 키이면 None을 반환한다."""
        node = self._find_node(key)
        if node is None:
            return None
        return node.data.value

    def contains(self, key: str) -> bool:
        """값이 None이어도 키가 저장되어 있으면 True를 반환한다."""
        return self._find_node(key) is not None

    def remove(self, key: str) -> bool:
        """키를 삭제하면 True, 없는 키이면 False를 반환한다."""
        node = self._find_node(key)
        if node is None:
            return False
        bucket = self._buckets[self._bucket_index(key)]
        bucket.remove_node(node)
        self._size -= 1
        return True

    def keys(self) -> List[str]:
        """모든 키를 새 배열에 담아 반환한다."""
        result = [""] * self._size
        index = 0
        for bucket in self._buckets:
            node = bucket.head
            while node is not None:
                result[index] = node.data.key
                index += 1
                node = node.next
        return result

    def _resize(self) -> None:
        """버킷을 두 배로 늘리고 모든 항목의 위치를 다시 계산한다."""
        old_buckets = self._buckets
        self._buckets = [DoublyLinkedList() for _ in range(len(old_buckets) * 2)]
        for bucket in old_buckets:
            node = bucket.head
            while node is not None:
                index = self._bucket_index(node.data.key)
                # 항목은 그대로 사용하고, 새 버킷에는 별도 노드로 연결한다.
                self._buckets[index].insert_back(node.data)
                node = node.next
