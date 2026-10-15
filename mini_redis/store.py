"""직접 만든 해시맵으로 문자열 키와 값을 관리하는 저장소."""

from typing import List, Optional

from mini_redis.hash_map import HashMap


class RedisStore:
    """기본 명령의 결과를 반환한다. 입력 해석과 화면 출력은 CLI가 맡는다."""

    def __init__(self) -> None:
        self._data = HashMap()

    def set(self, key: str, value: str) -> str:
        """문자열 값을 저장하거나 덮어쓰고 OK를 반환한다."""
        if not isinstance(value, str):
            raise TypeError("value must be a string")
        self._data.put(key, value)
        return "OK"

    def get(self, key: str) -> Optional[str]:
        """저장된 값을 반환한다. 없는 키이면 None을 반환한다."""
        return self._data.get(key)

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

    def _delete_entry(self, key: str) -> bool:
        """키를 삭제하는 공통 경로. 나중에 LRU와 TTL 정리도 이곳에 모은다."""
        return self._data.remove(key)
