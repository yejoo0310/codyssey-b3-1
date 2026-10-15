# Mini Redis

해시맵, 이중 연결 리스트, 최소 힙을 직접 구현하면서 CLI 기반의 메모리 저장소를 만드는 학습 프로젝트입니다.

현재는 **Phase 2: 체이닝 해시맵 구현**까지 완료한 상태입니다. CLI는 아직 Phase 0의 준비 안내를 출력하며, 명령어 입력은 Phase 4에서 구현합니다.

## 개발 환경과 실행

- Python 3.8 이상
- 외부 패키지 설치 없이 Python 표준 라이브러리 사용

프로젝트 루트에서 실행합니다.

```bash
python3 --version
python3 main.py
```

현재 출력:

```text
Mini Redis: Phase 0 준비 완료. 명령어 입력은 Phase 4에서 구현합니다.
```

전체 테스트 실행:

```bash
python3 -m unittest discover -v
```

현재 테스트는 `main.py`의 정상 실행, 이중 연결 리스트, 체이닝 해시맵의 동작을 확인합니다. 이후 각 자료구조와 명령어의 테스트를 추가합니다.

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
- [ ] 최소 힙: `push`, `pop`, `peek`, `size`, `_heapify_up`, `_heapify_down`
- [ ] 힙으로 가장 빠른 만료 시각 조회

### 명령어와 정책

- [ ] `SET`, `GET`, `DEL`, `EXISTS`, `DBSIZE`, `KEYS`
- [ ] 성공한 `SET`, `GET`에서 LRU 갱신
- [ ] `CONFIG SET maxmemory bytes`: 0은 무제한
- [ ] `INFO memory`: `used_memory`, `maxmemory`, `evicted_keys` 출력
- [ ] 메모리 사용량은 모든 키와 값의 UTF-8 바이트 수 합계로 계산
- [ ] `SET` 후 제한 초과 시 LRU 순서로 제거
- [ ] 단일 엔트리가 제한보다 크면 저장하지 않고 OOM 출력
- [ ] `EXPIRE`, `TTL`: 없는 키는 TTL -2, 만료 설정 없는 키는 -1
- [ ] 키 기반 명령은 만료 여부를 확인하고 만료된 키를 없는 키로 처리
- [ ] `SET` 덮어쓰기 시 기존 TTL 초기화
- [ ] 삭제 시 데이터·LRU·TTL·메모리 사용량을 함께 정리
- [ ] `mini-redis>` REPL, `exit`·`quit` 종료
- [ ] Redis 스타일 결과와 알 수 없는 명령·인자 개수·정수 파싱·OOM 에러
- [ ] 최소한 공백 없는 값 입력 지원
- [ ] 핵심 클래스와 함수에 주석 또는 docstring 작성

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
| 값 파싱 | 우선 공백 없는 값을 지원하고, 큰따옴표 값 지원은 CLI 단계에서 확장 여부를 결정합니다. |
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
