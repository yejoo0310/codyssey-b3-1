"""부모가 자식보다 크지 않도록 배열을 관리하는 최소 힙."""

from typing import Generic, List, Optional, TypeVar


T = TypeVar("T")


class MinHeap(Generic[T]):
    """서로 <로 비교할 수 있는 항목을 저장하고 가장 작은 항목부터 꺼낸다.

    TTL 예약에는 (만료 시각, 키) 튜플을 사용할 수 있다.
    내부 배열 전체가 정렬되는 것은 아니며, 최솟값만 맨 앞에 놓인다.
    """

    def __init__(self) -> None:
        self._items: List[T] = []

    def size(self) -> int:
        """저장된 항목 개수를 반환한다."""
        return len(self._items)

    def __len__(self) -> int:
        """len으로도 항목 개수를 확인할 수 있다."""
        return self.size()

    def peek(self) -> Optional[T]:
        """최솟값을 삭제하지 않고 확인한다. 비어 있으면 None을 반환한다."""
        if not self._items:
            return None
        return self._items[0]

    def push(self, item: T) -> None:
        """맨 뒤에 항목을 추가하고 부모와 비교하며 위로 올린다."""
        self._items.append(item)
        self._heapify_up(len(self._items) - 1)

    def pop(self) -> Optional[T]:
        """최솟값을 꺼내고 남은 항목을 정리한다. 비어 있으면 None을 반환한다."""
        if not self._items:
            return None
        smallest = self._items[0]
        last = self._items.pop()
        if self._items:
            # 마지막 항목으로 루트의 빈자리를 채우고 아래로 내려보낸다.
            self._items[0] = last
            self._heapify_down(0)
        return smallest

    def _heapify_up(self, index: int) -> None:
        """부모보다 작은 동안 두 항목을 바꿔 힙 조건을 복원한다."""
        while index > 0:
            parent = (index - 1) // 2
            if not self._items[index] < self._items[parent]:
                break
            self._items[index], self._items[parent] = (
                self._items[parent], self._items[index]
            )
            index = parent

    def _heapify_down(self, index: int) -> None:
        """더 작은 자식과 교환하며 힙 조건을 복원한다."""
        size = len(self._items)
        while True:
            left = 2 * index + 1
            right = left + 1
            if left >= size:
                break

            smaller = left
            if right < size and self._items[right] < self._items[left]:
                smaller = right
            if not self._items[smaller] < self._items[index]:
                break
            self._items[index], self._items[smaller] = (
                self._items[smaller], self._items[index]
            )
            index = smaller
