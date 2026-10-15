"""노드 참조를 사용해 O(1)에 삽입·삭제·이동하는 이중 연결 리스트."""

from typing import Any, Optional


class Node:
    """데이터와 앞뒤 노드의 참조를 보관한다."""

    def __init__(self, data: Any) -> None:
        self.data = data
        self.prev: Optional[Node] = None
        self.next: Optional[Node] = None
        # 소속을 기록하면 노드의 유효성을 리스트 순회 없이 검사할 수 있다.
        self._owner: Optional[DoublyLinkedList] = None


class DoublyLinkedList:
    """head는 맨 앞, tail은 맨 뒤 노드이며, 빈 상태에서는 둘 다 None이다.

    삽입은 새 노드를, 삭제는 분리한 노드를 반환한다.
    노드의 연결과 소속은 이 클래스의 메서드로만 변경해야 한다.
    """

    def __init__(self) -> None:
        self.head: Optional[Node] = None
        self.tail: Optional[Node] = None
        self._size = 0

    def __len__(self) -> int:
        """순회 없이 저장된 노드 개수를 반환한다. O(1)."""
        return self._size

    def _prepend(self, node: Node) -> None:
        """분리된 노드를 맨 앞에 연결한다. 내부에서만 사용하는 연산. O(1)."""
        node.prev = None
        node.next = self.head
        if self.head is None:
            self.tail = node
        else:
            self.head.prev = node
        self.head = node
        node._owner = self
        self._size += 1

    def insert_front(self, data: Any) -> Node:
        """데이터를 담은 새 노드를 맨 앞에 삽입하고 반환한다. O(1)."""
        node = Node(data)
        self._prepend(node)
        return node

    def insert_back(self, data: Any) -> Node:
        """데이터를 담은 새 노드를 맨 뒤에 삽입하고 반환한다. O(1)."""
        node = Node(data)
        node.prev = self.tail
        if self.tail is None:
            self.head = node
        else:
            self.tail.next = node
        self.tail = node
        node._owner = self
        self._size += 1
        return node

    def remove_front(self) -> Optional[Node]:
        """맨 앞 노드를 분리해 반환한다. 빈 리스트에서는 None. O(1)."""
        if self.head is None:
            return None
        return self.remove_node(self.head)

    def remove_back(self) -> Optional[Node]:
        """맨 뒤 노드를 분리해 반환한다. 빈 리스트에서는 None. O(1)."""
        if self.tail is None:
            return None
        return self.remove_node(self.tail)

    def _validate_node(self, node: Node) -> None:
        """이 리스트에 속한 노드인지 확인한다. O(1)."""
        if not isinstance(node, Node) or node._owner is not self:
            raise ValueError("node must belong to this list")

    def remove_node(self, node: Node) -> Node:
        """노드를 검색하지 않고 직접 분리해 반환한다. O(1).

        다른 리스트의 노드나 이미 삭제한 노드를 넘기면 ValueError가 발생한다.
        """
        self._validate_node(node)

        # A <-> node <-> B를 A <-> B로 바꾼다.
        # 이웃이 없는 경우에는 리스트의 head 또는 tail을 갱신한다.
        if node.prev is None:
            self.head = node.next
        else:
            node.prev.next = node.next

        if node.next is None:
            self.tail = node.prev
        else:
            node.next.prev = node.prev

        node.prev = None
        node.next = None
        node._owner = None
        self._size -= 1
        return node

    def move_to_front(self, node: Node) -> None:
        """기존 노드를 맨 앞으로 옮긴다. 노드 정체성과 전체 개수는 유지한다. O(1).

        다른 리스트의 노드나 이미 삭제한 노드를 넘기면 ValueError가 발생한다.
        """
        self._validate_node(node)
        if node is self.head:
            return
        self.remove_node(node)
        self._prepend(node)
