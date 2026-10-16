# Mini Redis

해시맵, 이중 연결 리스트, 최소 힙을 직접 구현하면서 CLI 기반의 메모리 저장소를 만드는 학습 프로젝트입니다.

현재는 **Phase 7: TTL과 만료 처리 구현**까지 완료한 상태입니다. 기본 명령 6개, 메모리 관리 명령 2개, TTL 명령 2개를 CLI에서 사용할 수 있습니다. Phase 8에서는 전체 기능을 통합 검증합니다.

## 개발 환경과 실행

- Python 3.8 이상
- 외부 패키지 설치 없이 Python 표준 라이브러리 사용

프로젝트 루트에서 실행합니다.

```bash
python3 --version
python3 main.py
```

실행 예시:

```text
mini-redis> SET name "Alice Kim"
OK
mini-redis> GET name
"Alice Kim"
mini-redis> EXISTS name
(integer) 1
mini-redis> DEL name
(integer) 1
mini-redis> GET name
(nil)
mini-redis> quit
```

전체 테스트 실행:

```bash
python3 -m unittest discover -v
```

현재 테스트는 연결 리스트·해시맵·최소 힙, 저장소와 LRU·메모리 제한·TTL, 명령 파싱과 출력, 실제 CLI 프로세스의 동작을 확인합니다. TTL 테스트는 실제로 기다리지 않고 시계를 직접 진행합니다.

## 파일별 역할

```text
main.py                      프로그램 실행 진입점
mini_redis/
    __init__.py              Python 패키지 표시
    linked_list.py           이중 연결 리스트 (Phase 1)
    hash_map.py              체이닝 해시맵 (Phase 2)
    store.py                 저장소와 LRU·메모리·TTL 정책 (Phase 3, 5, 7)
    cli.py                   입력 해석, 명령 실행 연결, 출력 (Phase 4)
    min_heap.py              최소 힙 (Phase 6)
tests/
    __init__.py              테스트 패키지 표시
    test_startup.py          프로그램 실행 확인
    test_linked_list.py      이중 연결 리스트 검증
    test_hash_map.py         체이닝 해시맵과 버킷 확장 검증
    test_store.py            기본 저장소 명령 조합 검증
    test_cli.py              파싱, 명령 실행, 출력 형식 검증
    test_memory.py           LRU, 메모리 계산, 자동 제거 검증
    test_min_heap.py         최소 힙의 순서와 경계 상황 검증
    test_ttl.py              TTL과 LRU·메모리 관리의 조합 검증
    helpers.py               테스트용 시계
```

`main.py`는 실행을 시작하고, `cli.py`는 사용자와의 입출력을 담당합니다. 실제 저장과 삭제는 `store.py`에서 처리하며, 각 자료구조는 독립된 모듈에 둡니다.

## 필수 요구사항 체크리스트

원본 과제 문서는 로컬의 `requirement.md`입니다. 다음은 구현할 항목의 요약입니다.

### 자료구조

- [x] 이중 연결 리스트: `prev`, `next`, `data`를 가진 노드
- [x] `insert_front`, `insert_back`, `remove_front`, `remove_back`, `remove_node`, `move_to_front`를 O(1)에 수행
- [x] 해시맵: 직접 만든 해시 함수와 체이닝 충돌 해결
- [x] `put`, `get`, `remove`, `contains`, `keys`, `size`
- [x] 로드 팩터 0.75 초과 시 버킷 수를 두 배로 확장하고 재해싱
- [x] 최소 힙: `push`, `pop`, `peek`, `size`, `_heapify_up`, `_heapify_down`
- [x] 힙으로 가장 빠른 만료 시각 조회와 저장소 연결

### 명령어와 정책

- [x] `SET`, `GET`, `DEL`, `EXISTS`, `DBSIZE`, `KEYS`의 저장소 기능과 CLI 연결
- [x] 성공한 `SET`, `GET`에서 LRU 갱신
- [x] `CONFIG SET maxmemory bytes`: 0은 무제한
- [x] `INFO memory`: `used_memory`, `maxmemory`, `evicted_keys` 출력
- [x] 메모리 사용량은 모든 키와 값의 UTF-8 바이트 수 합계로 계산
- [x] `SET` 후 제한 초과 시 LRU 순서로 제거
- [x] 단일 엔트리가 제한보다 크면 저장하지 않고 OOM 출력
- [x] `EXPIRE`, `TTL`: 없는 키는 TTL -2, 만료 설정 없는 키는 -1
- [x] 키 기반 명령은 만료 여부를 확인하고 만료된 키를 없는 키로 처리
- [x] `SET` 덮어쓰기 시 기존 TTL 초기화
- [x] 삭제 시 데이터·LRU·메모리 사용량을 함께 정리
- [x] 삭제 시 TTL 정보도 함께 정리
- [x] `mini-redis>` REPL, `exit`·`quit` 종료
- [x] Redis 스타일 결과와 알 수 없는 명령·인자 개수·닫히지 않은 따옴표 에러
- [x] 메모리 제한·EXPIRE의 정수 파싱 및 OOM 에러
- [x] 공백 없는 값과 큰따옴표로 감싼 값 입력 지원
- [x] 핵심 클래스와 함수에 주석 또는 docstring 작성

### 제약과 범위

- `dict`, `set`, `collections`를 사용하지 않습니다.
- `list`는 배열 저장소 용도로 제한적으로 사용하고, 해시맵과 힙의 알고리즘을 직접 구현합니다.
- 네트워크, 파일 영속성, 복잡 자료형, 멀티스레딩은 구현 범위에서 제외합니다.
- 동적 배열, 스택·큐·덱 문서화, 이진 트리 순회, BST, Pub/Sub는 선택 과제입니다. 필수 기능을 먼저 완성합니다.

## Phase와 커밋 단위

| Phase | 공부할 내용 | 작업과 완료 기준 | 커밋 메시지 예시 |
| --- | --- | --- | --- |
| 0 | 모듈, 패키지, 테스트 실행 | 구조와 요구사항 정리, 실행·테스트 성공 | `chore: 프로젝트 초기 구조 및 학습 계획 추가` |
| 1 | 노드와 양방향 참조 | 연결 리스트 구현, 빈 상태·노드 하나·삽입·삭제·이동 검증 | `feat: 이중 연결 리스트 구현 및 테스트 추가` |
| 2 | 해시, 충돌, 로드 팩터 | 체이닝 해시맵 구현, 충돌과 확장 후 데이터 유지 검증 | `feat: 체이닝 해시맵 및 버킷 확장 구현` |
| 3 | 자료구조와 저장소의 연결 | 기본 명령 6개 구현, 공통 삭제 경로 마련 | `feat: 기본 문자열 저장소 명령 구현` |
| 4 | REPL, 파싱, 에러 처리 | CLI에서 기본 명령 실행과 잘못된 입력 처리 | `feat: 명령어 입력 및 에러 처리 구현` |
| 5 | LRU, UTF-8 바이트 계산 | 메모리 명령과 자동 제거, 사용량·제거 횟수 검증 | `feat: LRU 제거 및 메모리 제한 구현` |
| 6 | 배열로 표현하는 완전 이진 트리 | 최소 힙 구현, 만료 시각 오름차순 추출 검증 | `feat: TTL 관리를 위한 최소 힙 구현` |
| 7 | 만료 시각과 지연 삭제 | TTL 명령 구현, 재설정·덮어쓰기·삭제와의 조합 검증 | `feat: TTL 명령 및 만료 처리 구현` |
| 8 | 통합 검증 | 전체 명령과 LRU·TTL 조합 검증, 사용 문서 완성 | `test: LRU 및 TTL 통합 동작 검증` |

각 Phase에서 작은 예시를 그린 뒤 구현하고, 경계 상황을 테스트하고, 동작 원리를 자기 말로 설명한 다음 커밋합니다. Phase 8의 문서 정리는 `docs: 실행 방법 및 구현 결정 정리`로 별도 커밋할 수 있습니다.

## 구현 전에 정한 동작

아래는 과제에서 선택할 수 있거나 세부적으로 명시하지 않은 부분에 대한 프로젝트의 초기 결정입니다. 구현하면서 변경한다면 이 문서와 테스트를 함께 수정합니다.

| 항목 | 결정 |
| --- | --- |
| 전체 조회 시 만료 처리 | `DBSIZE`, `KEYS`, `INFO memory` 전에 힙으로 만료 항목을 정리합니다. |
| 메모리 제한 축소 | 설정 시 즉시 제거하지 않고, 다음 성공한 `SET`에서 제한을 적용합니다. |
| 단일 엔트리 OOM | 기존 값을 변경하기 전에 크기를 검사하여 실패 시 기존 상태를 유지합니다. |
| LRU 갱신 | 성공한 `SET`, `GET`에서만 갱신합니다. |
| TTL 남은 초 | 양수인 남은 시간을 내림합니다. 만료 전 마지막 1초 미만은 0이 될 수 있습니다. |
| 0 이하의 EXPIRE | 존재하는 키를 즉시 삭제하고 1을 반환합니다. |
| 오래된 TTL 예약 | 지연 삭제를 사용합니다. 고유한 예약 번호로 현재 TTL과 일치하는지 확인하고 오래된 예약은 무시합니다. |
| 시간 측정 | `time.monotonic`을 기본으로 하고, 테스트에서는 시간 함수를 교체할 수 있게 합니다. |
| 값 파싱 | 공백으로 인자를 구분하고, 큰따옴표 안의 공백과 빈 문자열을 보존합니다. 큰따옴표 안에서는 `\"`와 `\\`를 각각 따옴표와 역슬래시 하나로 읽습니다. |
| 명령어 대소문자 | 명령어는 대소문자를 구분하지 않고, 키와 값은 입력 그대로 보존합니다. |

삭제 동작은 공통 경로로 모읍니다. `DEL`, TTL 만료, LRU 제거 모두 데이터·LRU·TTL·메모리를 함께 정리하고, `evicted_keys`는 LRU 제거일 때만 증가시킵니다.

## Phase 0에서 이해할 내용

- **모듈**: Python 파일 하나입니다. 예를 들어 `cli.py`에서 CLI 함수를 정의합니다.
- **패키지**: 관련 모듈을 모은 폴더입니다. `mini_redis/__init__.py`가 패키지의 시작 파일입니다.
- **import**: 다른 모듈의 기능을 가져옵니다. `main.py`는 `mini_redis.cli`의 `main` 함수를 가져옵니다.
- **클래스와 객체**: 클래스는 데이터와 동작을 묶는 틀이며, 객체는 그 틀로 만든 실제 대상입니다. Phase 1에서 노드와 리스트로 연습합니다.
- **객체 참조**: 변수는 객체를 가리킵니다. Phase 1의 `prev`, `next`는 이웃 노드를 가리키는 참조입니다.
- **테스트**: 기대한 동작을 코드로 확인합니다. 표준 라이브러리 `unittest`를 사용하고, 반복해서 확인할 수 있게 만듭니다.

Phase 0 완료 기준은 위 실행 명령과 테스트 명령이 성공하고, 각 파일의 역할과 다음 Phase의 범위를 설명할 수 있는 상태입니다.

## Phase 1에서 이해할 내용

각 노드는 앞 노드를 가리키는 `prev`, 뒤 노드를 가리키는 `next`, 저장할 값인 `data`를 가집니다. 리스트는 맨 앞인 `head`, 맨 뒤인 `tail`을 기억합니다. 비어 있으면 둘 다 `None`입니다.

```text
head                         tail
 ↓                            ↓
[A] <--------> [B] <--------> [C]
```

`B`를 삭제할 때는 `A.next`를 `C`로, `C.prev`를 `A`로 연결합니다. 삭제할 노드를 이미 알고 있으므로 검색할 필요가 없습니다. 모든 삽입·삭제·이동 메서드는 반복문 없이 정해진 수의 참조만 바꾸어 O(1)에 동작합니다. 반면 값을 보고 노드를 처음부터 찾는 작업은 O(n)입니다.

### 사용 예시

프로젝트 루트에서 `python3`를 실행한 뒤 다음 코드를 입력할 수 있습니다.

```python
from mini_redis.linked_list import DoublyLinkedList

linked = DoublyLinkedList()
alice = linked.insert_front("alice")
bob = linked.insert_front("bob")      # bob -> alice
linked.move_to_front(alice)           # alice -> bob
removed = linked.remove_back()        # bob 제거
print(removed.data)                    # bob
print(linked.head.data)                # alice
print(len(linked))                     # 1
```

### 메서드의 약속

| 메서드 | 결과 |
| --- | --- |
| `insert_front(data)`, `insert_back(data)` | 새로 만든 노드를 반환합니다. 이후 삭제·이동을 위해 참조를 보관할 수 있습니다. |
| `remove_front()`, `remove_back()` | 분리한 노드를 반환합니다. 빈 리스트에서는 `None`을 반환합니다. |
| `remove_node(node)` | 해당 노드를 분리해 반환하고 `prev`, `next`를 `None`으로 초기화합니다. |
| `move_to_front(node)` | 새 노드를 만들지 않고 기존 노드를 이동합니다. 반환값은 `None`이며 노드 개수는 유지됩니다. |
| `len(linked)` | 저장해 둔 노드 개수를 O(1)에 반환합니다. |

노드의 `_owner`는 소속 리스트를 기록하는 내부 필드입니다. 이를 통해 다른 리스트의 노드, 이미 삭제한 노드, 아직 삽입하지 않은 노드를 순회 없이 판별합니다. 잘못된 노드를 삭제하거나 이동하려 하면 `ValueError`가 발생합니다. 연결과 소속 필드는 직접 수정하지 않고 리스트의 메서드를 사용합니다.

Phase 1 테스트만 실행하려면 다음 명령을 사용합니다.

```bash
python3 -m unittest tests.test_linked_list -v
```

읽는 순서는 `Node` → `insert_front`와 `_prepend` → `insert_back` → `remove_node` → `move_to_front`를 권장합니다. 빈 리스트, 노드 하나, 가운데 노드 삭제에서 앞뒤 참조가 어떻게 바뀌는지 그려보세요. 향후 LRU에서는 맨 앞을 최근 사용한 키, 맨 뒤를 제거 대상으로 활용합니다.

## Phase 2에서 이해할 내용

해시맵은 문자열 키로 해시값을 만들고, 이를 버킷 개수로 나눈 나머지를 저장 위치로 사용합니다. 기본 버킷 수는 8개입니다. 각 버킷은 Phase 1의 `DoublyLinkedList`로 만들었습니다.

```text
문자열 키 → 직접 만든 해시 함수 → 해시값 % 버킷 개수

버킷 0: 비어 있음
버킷 1: (a, Alice) <-> (i, Iris) <-> (q, Quinn)
버킷 2: ...
```

서로 다른 키가 같은 버킷에 들어가는 것을 **충돌**이라고 합니다. 해당 버킷의 연결 리스트를 순회하며 실제 키를 비교해 항목을 구분하는 방식이 **체이닝**입니다. 해시값이나 버킷 위치가 같아도 같은 키라는 뜻은 아닙니다.

### 해시 함수와 버킷 확장

해시 함수는 문자마다 `이전 결과 × 31 + 문자 코드`를 계산합니다. 문자 순서가 결과에 반영되며, 매 단계에서 `0xFFFFFFFF`로 범위를 제한해 정수가 계속 커지지 않게 합니다. Python 내장 `hash`는 사용하지 않습니다.

**로드 팩터 = 키 개수 / 버킷 개수**입니다. 버킷이 4개라면 키 3개일 때는 0.75이므로 유지하고, 4번째 키를 추가하면 버킷을 8개로 늘립니다. 같은 키를 덮어쓸 때는 개수와 버킷 수가 바뀌지 않습니다.

버킷 수가 바뀌면 나머지 계산 결과도 달라질 수 있으므로 모든 키의 위치를 다시 계산합니다. 이것이 **재해싱**입니다. 항목과 값 객체는 유지하고, 새 버킷에는 별도의 연결 리스트 노드를 만듭니다. 재배치 중에는 키 개수를 늘리지 않습니다.

### 사용 예시와 메서드의 약속

```python
from mini_redis.hash_map import HashMap

mapping = HashMap(initial_capacity=4)
mapping.put("name", "Alice")
mapping.put("name", "Bob")       # 같은 키의 값만 변경
print(mapping.get("name"))       # Bob
print(mapping.size())            # 1
print(mapping.contains("name"))  # True
print(mapping.remove("name"))    # True
print(mapping.get("name"))       # None
```

| 메서드 | 결과 |
| --- | --- |
| `put(key, value)` | 키와 값을 저장합니다. 기존 키이면 값을 바꾸며, 반환값은 `None`입니다. |
| `get(key)` | 저장된 값을 반환합니다. 없는 키이면 `None`입니다. |
| `contains(key)` | 값이 `None`이어도 키가 있으면 `True`입니다. |
| `remove(key)` | 삭제하면 `True`, 없는 키이면 `False`입니다. |
| `keys()` | 모든 키를 새 배열로 반환합니다. 순서는 보장하지 않습니다. |
| `size()`, `len(mapping)` | 저장된 키 개수를 반환합니다. |
| `mapping.capacity` | 현재 버킷 개수를 읽는 속성입니다. |

키는 문자열만 받으며 다른 타입이면 `TypeError`가 발생합니다. 빈 문자열과 한글도 저장할 수 있습니다. 초기 버킷 수는 양의 정수만 허용하고, 잘못된 값이면 `ValueError`가 발생합니다.

키 길이를 일정하게 보면 조회·삽입·삭제는 평균 O(1)이며, 충돌이 몰리면 최악 O(n)입니다. 길이가 k인 키의 해시 계산에는 O(k)가 걸립니다. 버킷 확장이 발생한 삽입은 기존 항목 전체를 재배치해야 합니다. `keys()`는 모든 버킷과 항목을 확인하므로 버킷 수를 b라고 하면 O(b + n)입니다.

버킷 테이블과 키 목록에는 배열 용도의 `list`를 사용하며, 키 검색과 충돌 처리는 직접 구현합니다. `dict`, `set`, `collections`는 사용하지 않습니다.

Phase 2 테스트만 실행하려면 다음 명령을 사용합니다.

```bash
python3 -m unittest tests.test_hash_map -v
```

읽는 순서는 `_Entry` → `_hash` → `_bucket_index` → `_find_node` → `put`·`get`·`contains`·`remove` → `_resize`를 권장합니다. 확장 전후에 `a`, `e`, `i`, `m`의 버킷 위치가 어떻게 달라지는지 직접 계산해보세요.

## Phase 3에서 이해할 내용

`RedisStore`는 Phase 2의 `HashMap`에 문자열 키와 값을 저장하고, 기본 명령 6개의 결과를 반환합니다. 해시 함수와 충돌 처리는 해시맵에 맡기며, 저장소에서는 명령의 동작과 반환값을 정합니다.

```text
CLI (Phase 4) → RedisStore → HashMap → 버킷의 연결 리스트
```

저장소는 입력 문자열을 명령으로 나누거나 화면에 출력하지 않습니다. `GET`의 `None`을 `(nil)`로 바꾸거나 정수 앞에 `(integer)`를 붙이는 일은 CLI가 담당합니다. 저장소를 공부할 때는 Python에서 메서드를 직접 호출할 수도 있습니다.

### 사용 예시

프로젝트 루트에서 `python3`를 실행한 뒤 다음 코드를 입력합니다.

```python
from mini_redis.store import RedisStore

store = RedisStore()
print(store.set("name", "Alice"))  # OK
print(store.get("name"))           # Alice
print(store.set("name", "Bob"))    # OK: 기존 값 변경
print(store.dbsize())              # 1
print(store.exists("name"))        # 1
print(store.keys())                # ['name']
print(store.delete("name"))        # 1
print(store.get("name"))           # None
print(store.delete("name"))        # 0
```

### 명령과 메서드의 약속

| 명령 | 메서드 | 반환값 |
| --- | --- | --- |
| `SET key value` | `set(key, value)` | 새 저장과 덮어쓰기 모두 `"OK"` |
| `GET key` | `get(key)` | 저장된 문자열, 없는 키이면 `None` |
| `DEL key` | `delete(key)` | 삭제하면 정수 `1`, 없는 키이면 정수 `0` |
| `EXISTS key` | `exists(key)` | 있으면 정수 `1`, 없으면 정수 `0` |
| `DBSIZE` | `dbsize()` | 현재 키 개수 |
| `KEYS` | `keys()` | 전체 키를 담은 새 배열. 순서는 보장하지 않음 |

`del`은 Python 예약어이므로 메서드 이름은 `delete`로 정했습니다. 해시맵의 `remove`와 `contains`가 반환하는 참·거짓은 `int`로 변환해 명령에 맞는 정수 결과를 만듭니다.

해시맵은 다양한 값을 받을 수 있지만 저장소는 문자열만 허용합니다. 잘못된 값은 저장 전에 `TypeError`로 거부합니다. Phase 5부터 SET은 바이트 수를 계산하기 전에 키 타입도 검사하며, 다른 키 기반 명령은 해시맵의 검사를 재사용합니다. 숫자처럼 보이는 `"001"`도 그대로 보존하며, 빈 문자열과 한글도 저장할 수 있습니다. 값이 빈 문자열이어도 키는 존재합니다.

### 공통 삭제 경로

`delete()`는 `_delete_entry()`를 호출합니다. Phase 3에서는 해시맵 삭제만 담당했고, Phase 5에서는 LRU 노드와 메모리 사용량, Phase 7에서는 TTL 무효화도 함께 처리하도록 확장했습니다.

### 검증 방법

```bash
python3 -m unittest tests.test_store -v
python3 -m unittest discover -v
```

저장소 테스트는 덮어쓰기 후 키 개수, 삭제 후 전체 조회, 충돌한 키의 개별 삭제, 해시맵 확장 이후 여러 명령의 조합을 확인합니다. 잘못된 입력을 거부해도 기존 데이터가 유지되는지, 저장소 인스턴스끼리 데이터가 섞이지 않는지도 검증합니다.

읽는 순서는 `RedisStore.__init__` → `set`·`get` → `exists`·`dbsize`·`keys` → `delete`·`_delete_entry`를 권장합니다. 같은 키를 두 번 저장하거나 두 번 삭제할 때 반환값과 키 개수가 어떻게 달라지는지 먼저 예상해보세요.

## Phase 4에서 이해할 내용

REPL은 입력을 읽고(Read), 실행하고(Evaluate), 결과를 출력하는(Print) 과정을 반복(Loop)하는 구조입니다. `main()`이 시작할 때 저장소를 한 번 만들기 때문에 여러 명령 사이에 데이터가 유지됩니다.

```text
input → parse_command → 명령·인자 개수 확인 → RedisStore → 출력 형식 변환 → print
  ↑                                                                           |
  └──────────────────────────── 다음 입력 ──────────────────────────────────────┘
```

### 입력 규칙

- 명령어는 대소문자를 구분하지 않습니다. `get`, `GET`, `Get`은 같습니다.
- 키와 값은 대소문자, 한글, 이모지, 앞자리 0 등을 그대로 보존합니다.
- 공백이나 탭으로 인자를 구분합니다. 큰따옴표 안에서는 공백도 값의 일부입니다.
- `SET name "Alice Kim"`, `SET empty ""`, `SET "" ""`처럼 입력할 수 있습니다.
- 큰따옴표 안에서는 `\"`를 따옴표로, `\\`를 역슬래시 하나로 읽습니다. 그 밖의 역슬래시는 그대로 보존하며 `\n`을 실제 개행으로 바꾸지 않습니다.
- 작은따옴표는 그룹을 묶는 기능이 없으며 일반 문자로 취급합니다.
- 큰따옴표 앞뒤의 문자열은 한 인자로 이어집니다. `pre" "suffix`는 `pre suffix`입니다.
- `$HOME`, `$(date)`, `;`, `#` 같은 문자열을 셸 명령이나 주석으로 해석하지 않습니다.
- 빈 줄은 실행 결과 없이 다음 입력을 받습니다.

파서는 큰따옴표 안인지, 인자가 시작됐는지 따로 기억합니다. 그래서 `""`도 빈 인자 하나로 보존하고, 큰따옴표가 닫히지 않으면 저장소를 호출하기 전에 에러를 반환합니다.

### 실행과 출력의 약속

`execute_command(line, store)`는 명령 한 줄을 실행한 결과를 문자열로 반환합니다. 빈 줄은 `""`, 정상 종료 명령은 `None`을 반환합니다. `main()`은 이 결과에 따라 출력하거나 반복을 끝냅니다.

| 명령 | 인자 개수 | 출력 예시 |
| --- | --- | --- |
| `SET key value` | 2 | `OK` |
| `GET key` | 1 | `"Alice"`, 없는 키는 `(nil)` |
| `DEL key` | 1 | `(integer) 1` 또는 `(integer) 0` |
| `EXISTS key` | 1 | `(integer) 1` 또는 `(integer) 0` |
| `DBSIZE` | 0 | `(integer) 2` |
| `KEYS` | 0 | `1. "name"`처럼 번호를 붙인 목록, 없으면 `(empty array)` |
| `exit`, `quit` | 0 | 종료하며 별도 결과는 출력하지 않음 |

문자열은 `json.dumps`로 큰따옴표를 붙이고 내부 따옴표·역슬래시·제어 문자를 이스케이프합니다. 한글은 그대로 출력합니다. 이 함수는 문자열 표현에만 사용하며, 해시맵 저장이나 검색을 대신하지 않습니다. 빈 문자열은 `""`로 출력하고, `None`만 `(nil)`로 처리합니다.

### 에러와 종료

```text
mini-redis> HELLO
(error) ERR unknown command 'HELLO'
mini-redis> GET
(error) ERR wrong number of arguments for 'GET' command
mini-redis> SET name "Alice
(error) ERR unbalanced quotes in request
```

알 수 없는 명령과 잘못된 인자 수는 저장소를 호출하기 전에 검사합니다. 에러가 나도 프로그램은 다음 입력을 받고 기존 데이터는 유지됩니다. `quit extra`처럼 종료 명령에 인자를 붙이면 종료하지 않고 인자 오류를 출력합니다.

`exit`·`quit` 외에 Ctrl+D로 입력을 끝내거나 Ctrl+C를 눌러도 traceback 없이 종료합니다. 입력을 파이프로 전달한 경우에도 마지막 입력 후 정상 종료합니다. Phase 5에서 CONFIG SET maxmemory와 INFO memory를, Phase 7에서 EXPIRE·TTL을 추가했습니다.

### 검증 방법

```bash
python3 -m unittest tests.test_cli tests.test_startup -v
python3 -m unittest discover -v
```

단위 테스트는 파싱과 출력, 인자 검증, 에러 이후 데이터 보존을 확인합니다. 별도 프로세스로 실행하는 테스트는 프롬프트, 여러 명령 간 데이터 유지, 에러 복구, 빈 입력, quit·exit·입력 종료를 검증합니다.

읽는 순서는 `main` → `parse_command` → `execute_command`의 인자 검사 → 명령별 실행 → `_quote_string`을 권장합니다. 빈 값이 빈 입력과 어떻게 구분되는지, 잘못된 입력이 저장소에 도달하기 전에 어디서 차단되는지 따라가보세요.

## Phase 5에서 이해할 내용

LRU는 가장 오래 사용하지 않은 키부터 제거하는 정책입니다. 저장소가 키를 담은 이중 연결 리스트를 별도로 유지하고, 맨 앞을 최근 사용, 맨 뒤를 제거 대상으로 정합니다.

```text
해시맵: key → _StoredEntry(value, memory_size, lru_node)
                                               |
                                               ↓
LRU: [최근 사용한 키] <-> ... <-> [오래 사용하지 않은 키]
```

해시맵의 값이 문자열에서 `_StoredEntry` 객체로 바뀌었습니다. 저장된 문자열과 바이트 수, 해당 키의 LRU 노드 참조를 함께 보관합니다. 외부의 `get()`은 이 객체의 value만 반환하므로 기존 저장소 사용법은 같습니다.

### 언제 사용 순서를 바꾸는가?

- 새 키를 SET하면 LRU 맨 앞에 넣습니다.
- 기존 키를 SET하거나 GET에 성공하면 같은 노드를 맨 앞으로 옮깁니다.
- GET이 빈 문자열을 반환해도 성공이므로 순서를 갱신합니다.
- 없는 키의 GET과 EXISTS·DBSIZE·KEYS·INFO는 순서를 바꾸지 않습니다.
- 메모리 제한이 없어도 순서를 추적해, 나중에 제한을 설정했을 때 활용합니다.

항목이 LRU 노드를 직접 참조하므로 이동할 노드를 리스트에서 검색하지 않습니다. 노드 이동은 O(1)이며, 키를 찾는 해시맵 비용은 별도로 적용됩니다. 버킷 체이닝 노드와 LRU 노드는 서로 다른 노드입니다.

### 메모리 계산과 삭제

```text
항목 크기 = len(key.encode("utf-8")) + len(value.encode("utf-8"))
used_memory = 모든 항목 크기의 합계
```

`a`와 `가`를 저장하면 1 + 3 = 4바이트입니다. 따옴표 같은 입력 문법과 자료구조의 노드·버킷 비용은 계산하지 않습니다. 실제 Python 프로세스의 메모리 사용량과는 다릅니다.

덮어쓰기에서는 `새 크기 - 기존 크기`만 사용량에 반영합니다. 삭제할 때는 저장해 둔 크기를 빼고 LRU 노드도 분리합니다. LRU 자동 제거일 때만 `evicted_keys`를 1 늘립니다. DEL은 이 수치를 늘리지 않습니다.

### 새 명령어

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
```

각 항목이 2바이트입니다. a를 조회하면 b보다 최근 사용한 키가 되므로 c를 저장할 때 b가 제거됩니다. 한 번의 SET으로도 제한을 맞출 때까지 여러 키를 제거할 수 있습니다.

`CONFIG SET maxmemory bytes`는 0 이상의 십진 정수를 받습니다. `+4`처럼 부호를 붙일 수 있고 0은 무제한입니다. 음수, 소수, 밑줄, 16진수, 숫자가 아닌 문자열은 표준 정수 에러로 처리합니다. 큰따옴표로 감싼 숫자 안의 추가 공백도 허용하지 않습니다. 명령과 SET·maxmemory·memory 이름은 대소문자를 구분하지 않습니다.

제한을 현재 사용량보다 낮추더라도 바로 제거하지 않습니다. 다음 성공한 SET에서 새 사용량을 계산한 뒤 제거합니다. 따라서 제한을 낮춘 직후에는 INFO의 used_memory가 maxmemory보다 클 수 있습니다. 0으로 바꿔도 누적 제거 횟수는 유지됩니다.

단일 항목 자체가 제한을 초과하면 저장 전에 OOM으로 거부합니다.

```text
mini-redis> SET a 12345
(error) OOM command not allowed when used_memory > 'maxmemory'
```

OOM으로 실패한 SET은 살아 있는 기존 값과 TTL, LRU 순서, 제거 횟수를 바꾸지 않습니다. Phase 7부터는 명령 실행 전에 이미 만료된 키를 먼저 정리하므로, 실패한 SET에서도 만료된 키의 사용량은 줄어들 수 있습니다. LRU 맨 뒤부터 제거하는 작업은 유효한 SET으로 값을 반영한 후에만 실행합니다.

### Python에서 확인하기

```python
from mini_redis.store import RedisStore

store = RedisStore()
store.config_set_maxmemory(10)
store.set("가", "🔑")
info = store.info_memory()
print(info.used_memory)   # 7
print(info.maxmemory)     # 10
print(info.evicted_keys)  # 0
```

`MemoryInfo`는 세 숫자를 이름으로 읽을 수 있는 NamedTuple입니다. CLI는 그 결과를 받아 INFO 형식의 문자열로 출력합니다. 저장소에서 항목 하나가 너무 크면 `OutOfMemoryError`를 발생시키고, CLI가 이를 OOM 출력으로 변환합니다.

### 검증 방법

```bash
python3 -m unittest tests.test_memory tests.test_cli.MemoryCommandTests -v
python3 -m unittest discover -v
```

Phase 5 완료 시 전체 85개 테스트가 통과합니다. LRU 순서와 해시맵의 키 목록·개수, 메모리 통계를 함께 검증하며, 해시맵이 확장된 뒤에도 LRU 노드 참조가 유지되는지 확인합니다. 실제 CLI 프로세스에서도 자동 제거, OOM·정수 에러 이후의 복구를 확인합니다.

읽는 순서는 `_StoredEntry` → `RedisStore.set`·`get` → `_delete_entry` → `_evict_if_needed` → `config_set_maxmemory`·`info_memory` → CLI의 새 명령 분기를 권장합니다. 항목 크기와 사용 순서를 종이에 적고 어떤 키가 먼저 제거될지 예상해보세요.

## Phase 6에서 이해할 내용

최소 힙은 부모가 자식보다 크지 않도록 유지하는 완전 이진 트리입니다. 완전 이진 트리는 마지막 층을 제외하면 가득 차고, 마지막 층도 왼쪽부터 채웁니다. 노드 객체를 만들지 않고 배열의 인덱스로 부모와 자식을 표현합니다.

```text
배열: [2, 4, 3, 8, 6]

        2 (인덱스 0)
       / \
      4   3
     / \
    8   6
```

부모의 인덱스를 i라고 하면 왼쪽 자식은 `2 * i + 1`, 오른쪽 자식은 `2 * i + 2`입니다. 루트가 아닌 항목의 부모는 `(i - 1) // 2`로 찾습니다. 배열 전체가 정렬된 것은 아니지만 최솟값은 항상 루트인 인덱스 0에 있습니다.

### 삽입과 최솟값 제거

`push`는 배열 맨 뒤에 항목을 붙인 뒤, 부모보다 작으면 교환하며 올라갑니다. 이것이 `_heapify_up`입니다.

`pop`은 루트 값을 보관하고 배열 마지막 항목을 꺼내 루트의 빈자리를 채웁니다. 그 뒤 더 작은 자식과 교환하며 내려갑니다. 이것이 `_heapify_down`입니다. 왼쪽 자식만 있는 경우에는 왼쪽만 비교하고, 자식이 없으면 멈춥니다.

정렬 함수나 `heapq`로 힙의 동작을 대신하지 않습니다. 내장 `list`는 배열 저장소로 사용하며, 힙의 비교와 위치 교환은 직접 구현했습니다. 동적 배열 자체를 별도 클래스로 만드는 작업은 선택 과제입니다.

### 사용 예시

프로젝트 루트에서 `python3`를 실행한 뒤 입력할 수 있습니다.

```python
from mini_redis.min_heap import MinHeap

heap = MinHeap()
heap.push((30, "user:3"))
heap.push((10, "user:1"))
heap.push((20, "user:2"))
print(heap.peek())  # (10, 'user:1'): 삭제하지 않고 확인
print(heap.size())  # 3
print(heap.pop())   # (10, 'user:1')
print(heap.pop())   # (20, 'user:2')
print(heap.pop())   # (30, 'user:3')
print(heap.pop())   # None
```

| 메서드 | 결과 |
| --- | --- |
| `push(item)` | 항목을 추가합니다. 반환값은 `None`입니다. |
| `peek()` | 가장 작은 항목을 삭제하지 않고 반환합니다. 비어 있으면 `None`입니다. |
| `pop()` | 가장 작은 항목을 제거해 반환합니다. 비어 있으면 `None`입니다. |
| `size()`, `len(heap)` | 현재 항목 개수를 반환합니다. |

`MinHeap`은 서로 `<`로 비교할 수 있는 항목을 받습니다. `Generic[T]`와 `TypeVar`는 저장할 항목의 타입을 표현하는 힌트입니다. 한 힙 안에서는 일관되게 비교 가능한 값만 넣어야 하며, `None`은 빈 힙의 반환값으로 사용합니다. 서로 비교할 수 없는 타입을 섞는 입력은 지원하지 않습니다.

`(만료 시각, 키)` 튜플은 먼저 시각을 비교하고, 같으면 키 문자열을 비교합니다. 동일한 항목도 중복 저장할 수 있습니다. 향후 `(만료 시각, 키, 예약 번호)`처럼 비교 가능한 추가 정보를 넣을 수도 있습니다. 동일한 우선순위의 입력 순서까지 보장하는 안정 정렬은 제공하지 않습니다.

peek와 개수 조회는 O(1)입니다. 위로·아래로 이동하는 경로는 트리 높이만큼이므로 힙 정리의 비교·교환 비용은 O(log n)입니다. 내장 list의 크기 조정이 발생하면 배열 복사 비용이 추가될 수 있으며, 반복 연산에서는 분할 상환 비용으로 봅니다. 저장 공간은 O(n)입니다.

힙 클래스 자체는 실제 시간의 경과를 판단하거나 저장소의 키를 삭제하지 않습니다. Phase 7의 저장소가 현재 시각과 `peek()`의 만료 시각을 비교하고, 만료된 예약을 `pop()`으로 꺼내 공통 삭제 경로에 연결합니다.

### 검증 방법

```bash
python3 -m unittest tests.test_min_heap -v
python3 -m unittest discover -v
```

테스트는 빈 힙과 항목 하나, 다양한 삽입 순서, 중복과 같은 만료 시각, 왼쪽 자식만 남은 경우와 오른쪽이 더 작은 경우를 확인합니다. 고정된 난수 시드로 삽입과 삭제를 섞고, 매 단계에서 최솟값·개수·부모와 자식의 순서가 맞는지도 검증합니다.

읽는 순서는 `push` → `_heapify_up` → `peek` → `pop` → `_heapify_down`을 권장합니다. 배열과 트리를 나란히 그려 항목이 이동할 때 인덱스가 어떻게 바뀌는지 따라가보세요.

## Phase 7에서 이해할 내용

TTL은 키가 만료될 때까지 남은 시간입니다. 저장소 항목에 `expire_at`과 `expiry_id`를 추가하고, 최소 힙에는 `(만료 시각, 키, 예약 번호)`를 넣습니다. 기본 시계는 경과 시간 측정에 적합한 `time.monotonic`입니다.

```text
EXPIRE key seconds
  → 만료 시각 = 현재 시각 + seconds
  → 고유한 예약 번호 발급
  → 항목과 최소 힙에 예약 정보 기록

다음 저장소 명령
  → 힙의 가장 빠른 만료 시각 확인
  → 현재 시각 이하인 예약을 꺼냄
  → 현재 항목의 예약 번호·시각과 일치할 때만 공통 경로로 삭제
```

### 명령어와 반환값

| 명령 | Python 메서드 | 결과 |
| --- | --- | --- |
| `EXPIRE key seconds` | `expire(key, seconds)` | 존재하면 정수 1, 없거나 이미 만료됐으면 정수 0 |
| `TTL key` | `ttl(key)` | 남은 초, 만료 설정이 없으면 -1, 키가 없거나 만료됐으면 -2 |

EXPIRE의 seconds는 부호를 허용하는 십진 정수입니다. 0 이하는 존재하는 키를 즉시 삭제합니다. 소수·밑줄·16진수·잘못된 숫자 또는 표현 가능한 만료 시각을 넘는 값은 표준 정수 에러로 처리합니다. 잘못된 인자 수는 기존 CLI의 인자 오류 형식을 따릅니다.

TTL은 양수인 남은 시간을 내림합니다. 2.75초가 남으면 2, 1초 미만이면 0입니다. 만료 시각에 정확히 도달하면 키를 삭제하고 -2를 반환합니다. TTL 계산과 만료 판단은 같은 시각을 사용합니다.

```text
mini-redis> SET name Alice
OK
mini-redis> TTL name
(integer) -1
mini-redis> EXPIRE name 100
(integer) 1
mini-redis> SET name Bob
OK
mini-redis> TTL name
(integer) -1
mini-redis> EXPIRE name 0
(integer) 1
mini-redis> GET name
(nil)
mini-redis> TTL name
(integer) -2
```

### 만료는 언제 정리하는가?

키 기반 명령은 `_get_live_entry()`에서 만료 예약을 먼저 정리합니다. GET은 살아 있는 값에 성공한 경우에만 LRU를 갱신합니다. EXPIRE와 TTL 자체는 사용 순서를 바꾸지 않습니다.

DBSIZE·KEYS·INFO memory도 조회 전에 힙으로 만료된 키를 정리합니다. 따라서 별도로 GET하지 않은 만료 키도 개수와 목록, 사용량에서 제외됩니다. SET도 만료 정리를 먼저 하므로 이미 만료된 키 때문에 살아 있는 키를 불필요하게 LRU 제거하지 않습니다.

백그라운드 스레드는 사용하지 않습니다. 입력을 기다리는 동안에는 물리적인 삭제 작업을 하지 않고, 다음 유효한 저장소 명령에서 처리합니다. 시간상 만료된 키는 해당 명령에서 없는 키처럼 보입니다.

### 오래된 예약을 안전하게 무시하기

같은 키에 EXPIRE를 다시 실행하면 기존 힙 예약은 즉시 찾아 지우지 않고 남겨 둡니다. 이후 그 예약을 꺼낼 때 현재 항목의 예약 번호와 비교합니다. 이 방식이 지연 삭제입니다.

예약 번호는 저장소 전체에서 계속 증가하며 키를 삭제해도 초기화하지 않습니다. 그래서 DEL 후 같은 키를 다시 만들거나 LRU로 제거된 키를 재사용해도 예전 예약이 새 값을 삭제하지 않습니다. SET 덮어쓰기와 공통 삭제는 항목의 TTL을 즉시 무효화합니다.

힙에는 무효한 예약도 남을 수 있으므로 힙 항목 수가 저장된 키 개수보다 클 수 있습니다. 오래된 예약은 자신의 만료 시각이 지난 뒤 꺼내질 때 제거합니다. 이 힙 오버헤드는 과제의 used_memory 계산에는 포함하지 않습니다.

### LRU·메모리 상태와 함께 처리하기

만료 삭제와 0 이하 EXPIRE의 즉시 삭제도 `_delete_entry()`를 사용합니다. 해시맵·LRU·메모리 사용량·TTL 정보를 함께 정리하지만 `evicted_keys`는 늘리지 않습니다. 이 통계는 메모리 제한에 따른 LRU 제거만 셉니다.

단일 항목 OOM은 살아 있는 기존 값과 TTL을 유지합니다. 다만 이미 만료된 키는 쓰기 검사 전에 정리되므로 OOM 응답 직후 사용량이 줄어들 수 있습니다. 이는 LRU 제거가 아니라 만료 처리입니다.

### 기다리지 않고 시간 테스트하기

생성자의 clock 인자로 시간 함수를 전달할 수 있습니다. 다음 코드는 프로젝트 루트에서 실행할 수 있습니다.

```python
from mini_redis.store import RedisStore
from tests.helpers import ManualClock

clock = ManualClock()
store = RedisStore(clock=clock)
store.set("a", "1")
store.expire("a", 3)
print(store.ttl("a"))  # 3
clock.advance(2.5)
print(store.ttl("a"))  # 0: 아직 만료 전
clock.advance(0.5)
print(store.ttl("a"))  # -2: 정확히 만료
print(store.info_memory().used_memory)  # 0
```

EXPIRE의 예약 삽입은 힙 크기 h에 대해 O(log h)의 힙 비교·교환이 필요합니다. 각 명령 앞의 정리는 꺼내는 만료 예약 수에 비례합니다. 무효한 예약도 힙에서 꺼내야 하며, 전체 키 목록을 훑어 만료를 검사하지 않습니다. 해시맵 검색·문자열 처리 비용은 별도로 적용됩니다.

### 검증 방법

```bash
python3 -m unittest tests.test_ttl tests.test_cli.TTLCommandTests -v
python3 -m unittest discover -v
```

Phase 7 완료 시 전체 122개 테스트가 통과합니다. 정확한 만료 시각과 남은 초 내림, TTL 연장·단축, SET 초기화, DEL·LRU 제거 후 키 재사용, 같은 시각의 예약, 만료 정리와 메모리 제거의 조합을 검증합니다. 실제 CLI 프로세스에서도 TTL 명령과 에러 이후 복구를 확인합니다.

읽는 순서는 `expire` → `ttl` → `_get_live_entry` → `_expire_due` → `_delete_entry` → SET의 TTL 초기화 → CLI를 권장합니다. 동일한 키에 예약을 두 번 설정한 뒤 어떤 예약이 무효가 되는지 표로 적어보세요.
