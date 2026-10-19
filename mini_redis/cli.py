"""명령을 해석하고 저장소의 결과를 Redis 스타일로 출력한다."""

import json
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
    """공백으로 인자를 나누되, 큰따옴표 안의 공백과 빈 문자열은 보존한다."""
    tokens = []
    characters = []
    in_quotes = False
    token_started = False
    index = 0

    while index < len(line):
        character = line[index]
        if (
            character == "\\"
            and in_quotes
            and index + 1 < len(line)
            and line[index + 1] in ('"', "\\")
        ):
            # 큰따옴표 안의 \"와 \\는 해당 문자 하나로 읽는다.
            characters.append(line[index + 1])
            index += 2
            continue
        if character == '"':
            in_quotes = not in_quotes
            token_started = True
        elif character.isspace() and not in_quotes:
            if token_started:
                tokens.append("".join(characters))
                characters = []
                token_started = False
        else:
            characters.append(character)
            token_started = True
        index += 1

    if in_quotes:
        raise ValueError("unbalanced quotes in request")
    if token_started:
        tokens.append("".join(characters))
    return tokens


def _quote_string(value: str) -> str:
    """문자열을 큰따옴표로 감싸고 따옴표·개행 등을 안전하게 표시한다."""
    return json.dumps(value, ensure_ascii=False)


def _parse_integer(value: str) -> int:
    """부호가 있는 십진 정수를 읽는다. 밑줄이나 소수점은 허용하지 않는다."""
    digits = value[1:] if value.startswith(("+", "-")) else value
    if not digits or not digits.isascii() or not digits.isdecimal():
        raise ValueError("value is not an integer or out of range")
    return int(value)


def _parse_memory_limit(value: str) -> int:
    """메모리 제한에 사용할 0 이상의 정수를 읽는다."""
    limit = _parse_integer(value)
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
            seconds = _parse_integer(tokens[2])
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
        return "used_memory:{}\nmaxmemory:{}\nevicted_keys:{}".format(
            info.used_memory, info.maxmemory, info.evicted_keys
        )

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
