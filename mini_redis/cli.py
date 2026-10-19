"""명령을 해석하고 저장소의 결과를 Redis 스타일로 출력한다."""

import shlex
from typing import List, Optional

from mini_redis.store import OutOfMemoryError, RedisStore


# 명령어별 인자 개수.
_COMMAND_ARITIES = (
    ("SET", 2),
    ("GET", 1),
    ("DEL", 1),
    ("EXISTS", 1),
    ("DBSIZE", 0),
    ("KEYS", 0),
    ("CONFIG", 3),
    ("INFO", 1),
    ("EXPIRE", 2),
    ("TTL", 1),
    ("EXIT", 0),
    ("QUIT", 0),
)


def parse_command(line: str) -> List[str]:
    """shlex로 인자를 나누고 따옴표 안의 공백과 빈 문자열을 보존한다."""
    return shlex.split(line)


def _quote_string(value: str) -> str:
    """출력할 문자열을 큰따옴표로 감싼다."""
    return f'"{value}"'


def _parse_memory_limit(value: str) -> int:
    """메모리 제한에 사용할 0 이상의 정수를 읽는다."""
    limit = int(value)
    if limit < 0:
        raise ValueError("value is not an integer or out of range")
    return limit


def execute_command(line: str, store: RedisStore) -> Optional[str]:
    """한 줄을 실행해 출력 문자열을 반환한다. 종료 명령은 None을 반환한다."""
    try:
        tokens = parse_command(line)
    except ValueError as error:
        return "(error) ERR " + str(error)
    if not tokens:
        return ""

    command = tokens[0].upper()
    for name, arity in _COMMAND_ARITIES:
        if command == name:
            if len(tokens) - 1 != arity:
                return (
                    "(error) ERR wrong number of arguments "
                    "for '{}' command".format(command)
                )
            break
    else:
        return "(error) ERR unknown command '{}'".format(tokens[0])

    if command in ("EXIT", "QUIT"):
        return None
    if command == "SET":
        try:
            return store.set(tokens[1], tokens[2])
        except OutOfMemoryError as error:
            return "(error) OOM " + str(error)
    if command == "GET":
        value = store.get(tokens[1])
        # 빈 문자열도 유효한 값이므로 None일 때만 없는 키로 처리한다.
        return "(nil)" if value is None else _quote_string(value)
    if command == "DEL":
        return "(integer) {}".format(store.delete(tokens[1]))
    if command == "EXISTS":
        return "(integer) {}".format(store.exists(tokens[1]))
    if command == "DBSIZE":
        return "(integer) {}".format(store.dbsize())
    if command == "EXPIRE":
        try:
            seconds = int(tokens[2])
            result = store.expire(tokens[1], seconds)
        except ValueError:
            return "(error) ERR value is not an integer or out of range"
        return "(integer) {}".format(result)
    if command == "TTL":
        return "(integer) {}".format(store.ttl(tokens[1]))
    if command == "CONFIG":
        if tokens[1].upper() != "SET" or tokens[2].lower() != "maxmemory":
            return "(error) ERR unsupported CONFIG option"
        try:
            limit = _parse_memory_limit(tokens[3])
        except ValueError:
            return "(error) ERR value is not an integer or out of range"
        return store.config_set_maxmemory(limit)
    if command == "INFO":
        if tokens[1].lower() != "memory":
            return "(error) ERR unsupported INFO section"
        info = store.info_memory()
        return f"used_memory:{info.used_memory} maxmemory:{info.maxmemory} evicted_keys:{info.evicted_keys}"

    keys = store.keys()
    if not keys:
        return "(empty array)"
    return "\n".join(
        "{}. {}".format(index, _quote_string(key))
        for index, key in enumerate(keys, start=1)
    )


def main() -> None:
    """같은 저장소를 유지하며 입력·실행·출력을 반복한다."""
    store = RedisStore()
    while True:
        try:
            line = input("mini-redis> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        result = execute_command(line, store)
        if result is None:
            break
        if result:
            print(result)
