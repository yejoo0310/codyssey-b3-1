# Mini Redis 평가용 명령어

`python3 main.py`로 새로 실행한 뒤 아래 순서대로 입력합니다.

```text
SET name "Alice Kim"
GET name
EXISTS name
SET name Bob
GET name
DBSIZE
KEYS
DEL name
GET name
CONFIG SET maxmemory 4
SET a 1
SET b 2
GET a
SET c 3
GET b
INFO memory
SET a 1234
CONFIG SET maxmemory 0
SET session active
EXPIRE session 60
TTL session
SET session renewed
TTL session
EXPIRE session 0
GET session
TTL session
EXPIRE missing 10
HELLO
GET
CONFIG SET maxmemory abc
quit
```

## 예상 출력

명령 순서대로 대응하며, `quit`은 출력 없이 종료합니다.

```text
OK
"Alice Kim"
(integer) 1
OK
"Bob"
(integer) 1
1. "name"
(integer) 1
(nil)
OK
OK
OK
"1"
OK
(nil)
used_memory:4 maxmemory:4 evicted_keys:1
(error) OOM command not allowed when used_memory > 'maxmemory'
OK
OK
(integer) 1
(integer) 59
OK
(integer) -1
(integer) 1
(nil)
(integer) -2
(integer) 0
(error) ERR unknown command 'HELLO'
(error) ERR wrong number of arguments for 'GET' command
(error) ERR value is not an integer or out of range
```

첫 `TTL session`의 `59`는 EXPIRE 직후 실행했을 때의 예시입니다. 실제 출력은 입력까지 걸린 시간에 따라 달라집니다. 만료 후에는 `-2`가 나오므로 TTL 관련 명령은 이어서 입력하세요.
