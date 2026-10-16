"""직접 만든 해시맵으로 문자열 키와 값을 관리하는 저장소."""

from typing import List, NamedTuple, Optional

from mini_redis.hash_map import HashMap
from mini_redis.linked_list import DoublyLinkedList, Node


class OutOfMemoryError(Exception):
    """항목 하나의 크기가 메모리 제한을 넘을 때 발생한다."""


class MemoryInfo(NamedTuple):
    """메모리 사용량, 제한, LRU로 제거한 키 개수를 묶는다."""

    used_memory: int
    maxmemory: int
    evicted_keys: int


class _StoredEntry:
    """값과 바이트 수, 해당 키의 LRU 노드를 보관한다."""

    def __init__(self, value: str, memory_size: int, lru_node: Node) -> None:
        self.value = value
        self.memory_size = memory_size
        self.lru_node = lru_node


class RedisStore:
    """기본 명령의 결과를 반환한다. 입력 해석과 화면 출력은 CLI가 맡는다."""

    def __init__(self) -> None:
        self._data = HashMap()
        self._lru = DoublyLinkedList()
        self._used_memory = 0
        self._maxmemory = 0
        self._evicted_keys = 0

    def set(self, key: str, value: str) -> str:
        """문자열 값을 저장하거나 덮어쓰고 OK를 반환한다."""
        if not isinstance(key, str):
            raise TypeError("key must be a string")
        if not isinstance(value, str):
            raise TypeError("value must be a string")
        memory_size = len(key.encode("utf-8")) + len(value.encode("utf-8"))
        # 실패한 쓰기로 기존 값이나 LRU 순서가 바뀌지 않게 먼저 검사한다.
        if self._maxmemory > 0 and memory_size > self._maxmemory:
            raise OutOfMemoryError(
                "command not allowed when used_memory > 'maxmemory'"
            )

        entry = self._data.get(key)
        if entry is None:
            node = self._lru.insert_front(key)
            self._data.put(key, _StoredEntry(value, memory_size, node))
            self._used_memory += memory_size
        else:
            self._used_memory += memory_size - entry.memory_size
            entry.value = value
            entry.memory_size = memory_size
            self._lru.move_to_front(entry.lru_node)
        self._evict_if_needed()
        return "OK"

    def get(self, key: str) -> Optional[str]:
        """저장된 값을 반환한다. 없는 키이면 None을 반환한다."""
        entry = self._data.get(key)
        if entry is None:
            return None
        self._lru.move_to_front(entry.lru_node)
        return entry.value

    def delete(self, key: str) -> int:
        """키를 삭제하면 1, 없는 키이면 0을 반환한다."""
        return int(self._delete_entry(key))

    def exists(self, key: str) -> int:
        """키가 있으면 1, 없으면 0을 반환한다."""
        return int(self._data.contains(key))

    def dbsize(self) -> int:
        """현재 저장된 키 개수를 반환한다."""
        return self._data.size()

    def keys(self) -> List[str]:
        """전체 키를 새 배열로 반환한다. 순서는 보장하지 않는다."""
        return self._data.keys()

    def config_set_maxmemory(self, limit: int) -> str:
        """0 이상의 메모리 제한을 설정한다. 0은 무제한이다."""
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 0:
            raise ValueError("value is not an integer or out of range")
        # 제한을 낮춰도 다음 성공한 SET에서 제거를 수행한다.
        self._maxmemory = limit
        return "OK"

    def info_memory(self) -> MemoryInfo:
        """현재 메모리 정보를 반환한다. 사용 순서는 바꾸지 않는다."""
        return MemoryInfo(self._used_memory, self._maxmemory, self._evicted_keys)

    def _evict_if_needed(self) -> None:
        """제한 이하가 될 때까지 가장 오래 사용하지 않은 키부터 제거한다."""
        while self._maxmemory > 0 and self._used_memory > self._maxmemory:
            self._delete_entry(self._lru.tail.data, evicted=True)

    def _delete_entry(self, key: str, *, evicted: bool = False) -> bool:
        """데이터와 LRU, 사용량을 함께 정리하는 공통 삭제 경로."""
        entry = self._data.get(key)
        if entry is None:
            return False
        self._data.remove(key)
        self._lru.remove_node(entry.lru_node)
        self._used_memory -= entry.memory_size
        if evicted:
            self._evicted_keys += 1
        return True
