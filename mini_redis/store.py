"""직접 만든 해시맵으로 문자열 키와 값을 관리하는 저장소."""

import math
import time
from typing import List, NamedTuple, Optional

from mini_redis.hash_map import HashMap
from mini_redis.linked_list import DoublyLinkedList, Node
from mini_redis.min_heap import MinHeap


class OutOfMemoryError(Exception):
    """항목 하나의 크기가 메모리 제한을 넘을 때 발생한다."""


class MemoryInfo(NamedTuple):
    """메모리 사용량, 제한, LRU로 제거한 키 개수를 묶는다."""

    used_memory: int
    maxmemory: int
    evicted_keys: int


class _StoredEntry:
    """값과 바이트 수, LRU 노드와 현재 만료 예약을 보관한다."""

    def __init__(self, value: str, memory_size: int, lru_node: Node) -> None:
        self.value = value
        self.memory_size = memory_size
        self.lru_node = lru_node
        self.expire_at: Optional[float] = None
        self.expiry_id: Optional[int] = None


class RedisStore:
    """기본 명령의 결과를 반환한다. 입력 해석과 화면 출력은 CLI가 맡는다."""

    def __init__(self) -> None:
        self._data = HashMap()
        self._lru = DoublyLinkedList()
        self._used_memory = 0
        self._maxmemory = 0
        self._evicted_keys = 0
        self._expiry_heap: MinHeap = MinHeap()
        self._next_expiry_id = 0

    def set(self, key: str, value: str) -> str:
        """문자열 값을 저장하거나 덮어쓰고 OK를 반환한다."""
        if not isinstance(key, str):
            raise TypeError("key must be a string")
        if not isinstance(value, str):
            raise TypeError("value must be a string")
        memory_size = len(key.encode("utf-8")) + len(value.encode("utf-8"))
        entry = self._get_live_entry(key)
        # OOM으로 살아 있는 값이나 사용 순서가 바뀌지 않게 먼저 검사한다.
        if self._maxmemory > 0 and memory_size > self._maxmemory:
            raise OutOfMemoryError(
                "command not allowed when used_memory > 'maxmemory'"
            )

        if entry is None:
            node = self._lru.insert_front(key)
            self._data.put(key, _StoredEntry(value, memory_size, node))
            self._used_memory += memory_size
        else:
            self._used_memory += memory_size - entry.memory_size
            entry.value = value
            entry.memory_size = memory_size
            entry.expire_at = None
            entry.expiry_id = None
            self._lru.move_to_front(entry.lru_node)
        self._evict_if_needed()
        return "OK"

    def get(self, key: str) -> Optional[str]:
        """저장된 값을 반환한다. 없는 키이면 None을 반환한다."""
        entry = self._get_live_entry(key)
        if entry is None:
            return None
        self._lru.move_to_front(entry.lru_node)
        return entry.value

    def delete(self, key: str) -> int:
        """키를 삭제하면 1, 없는 키이면 0을 반환한다."""
        self._get_live_entry(key)
        return int(self._delete_entry(key))

    def exists(self, key: str) -> int:
        """키가 있으면 1, 없으면 0을 반환한다."""
        return int(self._get_live_entry(key) is not None)

    def dbsize(self) -> int:
        """현재 저장된 키 개수를 반환한다."""
        self._expire_due()
        return self._data.size()

    def keys(self) -> List[str]:
        """전체 키를 새 배열로 반환한다. 순서는 보장하지 않는다."""
        self._expire_due()
        return self._data.keys()

    def expire(self, key: str, seconds: int) -> int:
        """만료 시간을 설정한다. 0 이하는 즉시 삭제하며, 없는 키이면 0이다."""
        if not isinstance(seconds, int) or isinstance(seconds, bool):
            raise ValueError("value is not an integer or out of range")
        now = time.monotonic()
        entry = self._get_live_entry(key, now)
        if entry is None:
            return 0
        if seconds <= 0:
            self._delete_entry(key)
            return 1

        try:
            expire_at = now + seconds
        except OverflowError:
            raise ValueError("value is not an integer or out of range") from None
        if not math.isfinite(expire_at):
            raise ValueError("value is not an integer or out of range")

        # 삭제 후 같은 키를 다시 써도 예전 예약과 겹치지 않게 한다.
        self._next_expiry_id += 1
        self._expiry_heap.push((expire_at, key, self._next_expiry_id))
        entry.expire_at = expire_at
        entry.expiry_id = self._next_expiry_id
        return 1

    def ttl(self, key: str) -> int:
        """남은 초를 내림해 반환한다. 없는 키는 -2, 만료 설정이 없으면 -1이다."""
        now = time.monotonic()
        entry = self._get_live_entry(key, now)
        if entry is None:
            return -2
        if entry.expire_at is None:
            return -1
        return int(entry.expire_at - now)

    def config_set_maxmemory(self, limit: int) -> str:
        """0 이상의 메모리 제한을 설정한다. 0은 무제한이다."""
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 0:
            raise ValueError("value is not an integer or out of range")
        self._expire_due()
        # 제한을 낮춰도 다음 성공한 SET에서 제거를 수행한다.
        self._maxmemory = limit
        return "OK"

    def info_memory(self) -> MemoryInfo:
        """현재 메모리 정보를 반환한다. 사용 순서는 바꾸지 않는다."""
        self._expire_due()
        return MemoryInfo(self._used_memory, self._maxmemory, self._evicted_keys)

    def _get_live_entry(
        self, key: str, now: Optional[float] = None
    ) -> Optional[_StoredEntry]:
        """만료된 항목을 먼저 정리하고 현재 키의 항목을 찾는다."""
        if not isinstance(key, str):
            raise TypeError("key must be a string")
        self._expire_due(now)
        return self._data.get(key)

    def _expire_due(self, now: Optional[float] = None) -> None:
        """힙에서 만료된 예약을 꺼내며, 현재도 유효한 예약의 키만 삭제한다."""
        if now is None:
            now = time.monotonic()
        while True:
            reservation = self._expiry_heap.peek()
            if reservation is None or reservation[0] > now:
                break
            expire_at, key, expiry_id = self._expiry_heap.pop()
            entry = self._data.get(key)
            if (
                entry is not None
                and entry.expiry_id == expiry_id
                and entry.expire_at == expire_at
            ):
                self._delete_entry(key)

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
        entry.expire_at = None
        entry.expiry_id = None
        if evicted:
            self._evicted_keys += 1
        return True
