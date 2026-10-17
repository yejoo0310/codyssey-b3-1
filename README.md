# Mini Redis

해시맵, 이중 연결 리스트, 최소 힙을 직접 구현한 CLI 기반 In-Memory Key-Value 저장소입니다. 문자열 저장·조회와 LRU 기반 메모리 관리, TTL 기반 만료 처리를 지원합니다.

## 실행 환경

- Python 3.8 이상을 대상으로 작성했습니다.
- Python 표준 라이브러리만 사용하므로 별도 패키지 설치가 필요하지 않습니다.
- 실행 검증 환경은 Python 3.10.10입니다. Python 3.8 문법 호환성은 AST 파싱으로 확인했으며, Python 3.8 인터프리터에서 별도로 실행하지는 않았습니다.

프로젝트 루트에서 실행합니다.

```bash
python3 main.py
```

`mini-redis>` 프롬프트에 명령을 입력하며, `exit` 또는 `quit`으로 종료합니다. 초기 상태는 빈 저장소이며 메모리 제한은 없습니다. 종료하면 데이터는 사라집니다.

## 지원 명령

| 분류 | 명령 | 동작 및 출력 |
| --- | --- | --- |
| 기본 | `SET key value` | 저장하거나 덮어쓰고 `OK`. 기존 TTL 초기화, LRU 갱신 |
| 기본 | `GET key` | 존재하면 큰따옴표로 감싼 값과 LRU 갱신, 없거나 만료되면 `(nil)` |
| 기본 | `DEL key` | 삭제하면 `(integer) 1`, 없으면 `(integer) 0` |
| 기본 | `EXISTS key` | 존재하면 `(integer) 1`, 없으면 `(integer) 0` |
| 기본 | `DBSIZE` | 만료된 키를 정리한 뒤 `(integer) N` |
| 기본 | `KEYS` | 전체 키를 번호가 있는 목록으로 출력. 없으면 `(empty array)` |
| 메모리 | `CONFIG SET maxmemory bytes` | 0 이상의 정수로 제한 설정 후 `OK`. 0은 무제한 |
| 메모리 | `INFO memory` | `used_memory`, `maxmemory`, `evicted_keys` 출력 |
| TTL | `EXPIRE key seconds` | 존재하면 만료 시간 설정 후 `(integer) 1`, 없으면 `(integer) 0` |
| TTL | `TTL key` | 남은 초를 내림한 정수. 만료 설정이 없으면 -1, 키가 없으면 -2 |

명령과 하위 옵션은 대소문자를 구분하지 않으며 키와 값은 입력 그대로 보존합니다. 공백 없는 값, 큰따옴표로 감싼 공백 포함 값, 빈 문자열을 지원합니다. `KEYS`의 출력 순서는 보장하지 않으며 패턴 인자는 받지 않습니다. 키 기반 명령은 한 번에 키 하나만 처리합니다.

## 사용 예시

### 기본 저장과 삭제

```text
mini-redis> SET name "Alice Kim"
OK
mini-redis> GET name
"Alice Kim"
mini-redis> EXISTS name
(integer) 1
mini-redis> DBSIZE
(integer) 1
mini-redis> KEYS
1. "name"
mini-redis> DEL name
(integer) 1
mini-redis> GET name
(nil)
mini-redis> KEYS
(empty array)
```

### 메모리 제한과 LRU 제거

새로 실행한 저장소에서 입력합니다. 각 항목은 키 1바이트와 값 1바이트를 합쳐 2바이트입니다. `GET a`로 a를 최근 사용한 키로 갱신하면, c를 저장할 때 오래된 b가 제거됩니다.

```text
mini-redis> CONFIG SET maxmemory 4
OK
mini-redis> SET a 1
OK
mini-redis> SET b 2
OK
mini-redis> GET a
"1"
mini-redis> SET c 3
OK
mini-redis> GET b
(nil)
mini-redis> INFO memory
used_memory:4
maxmemory:4
evicted_keys:1
mini-redis> SET a 1234
(error) OOM command not allowed when used_memory > 'maxmemory'
mini-redis> GET a
"1"
```

마지막 SET의 항목은 키와 값 합계가 5바이트이므로 거절되고 기존 a의 값은 유지됩니다.

### TTL과 덮어쓰기

```text
mini-redis> SET session active
OK
mini-redis> TTL session
(integer) -1
mini-redis> EXPIRE session 60
(integer) 1
mini-redis> SET session renewed
OK
mini-redis> TTL session
(integer) -1
mini-redis> EXPIRE session 0
(integer) 1
mini-redis> GET session
(nil)
mini-redis> TTL session
(integer) -2
mini-redis> EXPIRE missing 10
(integer) 0
```

자연 만료는 `SET temp value` → `EXPIRE temp 2` 입력 후 3초 이상 기다렸다가 `GET temp`가 `(nil)`, `TTL temp`가 `(integer) -2`인지 확인할 수 있습니다. 양수 TTL은 명령 입력까지의 경과 시간에 따라 달라집니다.

## 메모리·LRU·TTL 처리 정책

### 메모리 사용량

```text
used_memory = Σ(len(key.encode("utf-8")) + len(value.encode("utf-8")))
```

노드·포인터·버킷 등의 오버헤드는 제외하며 실제 프로세스 메모리를 측정하지 않습니다. 예를 들어 `가` → `🔑`는 3 + 4 = 7바이트입니다.

- 성공한 SET 이후 제한을 초과하면 LRU 키부터 제한 이하가 될 때까지 반복 제거합니다.
- 단일 항목 자체가 제한보다 크면 OOM으로 거절하며 기존의 살아 있는 값과 LRU 순서를 보존합니다. 명령 처리 중 이미 만료된 항목은 정리될 수 있습니다.
- `evicted_keys`는 메모리 제한에 따른 LRU 제거만 누적합니다. DEL과 TTL 삭제는 이 값을 늘리지 않습니다.
- 제한을 현재 사용량보다 낮추면 즉시 제거하지 않고 다음 성공한 SET에서 적용합니다.
- 성공한 SET과 GET만 최근 사용 순서를 갱신합니다. EXISTS, TTL 등의 조회는 갱신하지 않습니다.

### 만료 처리

- `time.monotonic()`을 기준으로 절대 만료 시각을 계산합니다.
- 백그라운드 작업 없이 다음 저장소 명령에서 힙의 만료 예약을 정리합니다. 만료된 키는 없는 키처럼 처리하며 GET의 LRU 갱신 대상이 되지 않습니다.
- `EXPIRE`의 초가 0 이하이면 존재하는 키를 즉시 삭제합니다.
- SET 덮어쓰기는 기존 TTL을 초기화합니다.
- TTL의 남은 시간은 내림하므로 만료 직전 1초 미만에는 0을 반환할 수 있습니다.
- DEL·자연 만료·LRU 제거는 공통 삭제 경로로 데이터와 LRU 노드, 사용량, 현재 TTL 정보를 정리합니다.
- 힙에는 `(expire_at, key, expiry_id)`를 저장합니다. TTL 재설정·삭제·덮어쓰기 이후 남은 옛 예약은 현재 엔트리의 예약 ID와 시각을 비교해 무시합니다. 무효한 예약은 해당 시각까지 힙에 남을 수 있습니다.

## 에러 처리

에러를 출력한 뒤에도 REPL은 다음 입력을 받습니다.

```text
mini-redis> HELLO
(error) ERR unknown command 'HELLO'
mini-redis> GET
(error) ERR wrong number of arguments for 'GET' command
mini-redis> CONFIG SET maxmemory abc
(error) ERR value is not an integer or out of range
mini-redis> CONFIG SET maxmemory -1
(error) ERR value is not an integer or out of range
mini-redis> EXPIRE key 1.5
(error) ERR value is not an integer or out of range
mini-redis> SET key "unfinished
(error) ERR unbalanced quotes in request
```

## 구현 구조

```text
main.py                     REPL 실행 진입점
mini_redis/
    linked_list.py          노드와 이중 연결 리스트
    hash_map.py             직접 구현한 해시 함수와 체이닝 해시맵
    min_heap.py             배열 기반 최소 힙
    store.py                문자열 저장소, LRU, 메모리 제한, TTL
    cli.py                  명령 파싱, 인자 검증, 실행 연결, 출력
tests/
    test_linked_list.py     삽입·삭제·이동과 경계 노드
    test_hash_map.py        충돌 처리와 버킷 확장
    test_min_heap.py        최솟값과 힙 조건
    test_store.py           기본 명령과 값 보존
    test_memory.py          UTF-8 사용량, LRU, 연속 제거, OOM
    test_ttl.py             만료 경계와 재설정·삭제·키 재사용
    test_cli.py             파싱, 인자 수, 정수 오류, 출력
    test_startup.py         실제 프로세스, 프롬프트, 종료, 오류 복구
    test_integration.py     여러 명령과 내부 자료구조의 상태 일관성
    helpers.py              테스트용 수동 시계
```

### 직접 구현한 자료구조

| 자료구조 | 주요 메서드 | 구현 방식 |
| --- | --- | --- |
| 이중 연결 리스트 | `insert_front`, `insert_back`, `remove_front`, `remove_back`, `remove_node`, `move_to_front` | `prev`, `next`, `data`를 가진 노드. 참조를 이용한 삽입·삭제·이동은 O(1) |
| 해시맵 | `put`, `get`, `remove`, `contains`, `keys`, `size` | 직접 만든 해시 함수와 이중 연결 리스트를 이용한 체이닝. 로드 팩터 0.75 초과 시 버킷 수를 두 배로 확장하고 재해싱 |
| 최소 힙 | `push`, `pop`, `peek`, `size`, `_heapify_up`, `_heapify_down` | 배열로 완전 이진 트리 표현. 최솟값 조회 O(1), 힙 경로를 따르는 삽입·삭제 O(log n). 내부 배열 확장 비용은 별도 |

해시 함수는 각 문자에 대해 `result = (result * 31 + ord(character)) & 0xFFFFFFFF`를 계산합니다. 해시맵의 키 조회는 버킷이 고르게 분산될 때 평균 O(1)이며 충돌이 몰리면 O(n)입니다. 해시 계산에는 키 길이에 비례하는 비용이 듭니다.

저장소 엔트리는 자신의 LRU 노드를 직접 참조합니다. 해시맵으로 엔트리를 찾은 뒤 리스트를 순회하지 않고 노드를 이동·삭제합니다. 명령 전체에는 해시 계산, 재해싱, 만료 예약 정리나 여러 키 제거 비용이 추가될 수 있습니다.

프로덕션 코드에서는 `dict`, `set`, `collections`, `heapq`로 자료구조를 대체하지 않습니다. `list`는 버킷과 힙의 배열 저장소 및 결과 목록 등에 사용합니다. 핵심 클래스와 함수에는 주석 또는 docstring을 작성했습니다.

## 테스트

프로젝트 루트에서 전체 테스트를 실행합니다.

```bash
python3 -m unittest discover -v
```

총 125개 테스트가 자료구조, 기본 명령, 파싱·에러 처리, LRU·메모리 제한, TTL, 실제 CLI 프로세스를 검증합니다. TTL 테스트는 실제로 기다리지 않고 수동 시계를 주입해 정확한 만료 시각과 경계를 확인합니다.

```bash
# TTL과 만료 경계
python3 -m unittest tests.test_ttl -v

# 통합 시나리오와 실제 CLI 실행
python3 -m unittest tests.test_integration tests.test_startup -v
```

통합 테스트는 명령 반환값뿐 아니라 해시맵의 키·값, LRU의 양방향 연결과 노드 참조, 현재 TTL 예약, 사용량과 누적 제거 횟수를 함께 검사합니다. 해시맵 확장, TTL 재설정, 덮어쓰기, 삭제, 자연 만료, 메모리 제한 축소와 연속 LRU 제거를 조합한 시나리오도 포함합니다.

## 구현 범위

필수 자료구조와 문자열 명령 6개, 메모리 관리 명령 2개, TTL 명령 2개, CLI 및 에러 처리를 구현했습니다.

네트워크 통신, 파일 영속성, 복잡 자료형, 멀티스레딩·락, 실제 Redis의 추가 옵션과 다중 키 문법은 포함하지 않습니다. 선택 과제인 동적 배열 별도 구현, 스택·큐·덱 문서화, 이진 트리 순회, BST, Pub/Sub는 구현하지 않았습니다.
