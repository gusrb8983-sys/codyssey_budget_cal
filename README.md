# 나만의 용돈 기입장

터미널에서 쓰는 콘솔 가계부입니다. 수입/지출을 JSONL 파일에 저장하고,
검색, 월별 요약, 예산 초과 경고, CSV 가져오기/내보내기를 지원합니다.

## 실행 방법

- Python 3.10 이상, 표준 라이브러리만 사용합니다 (pip 설치 없음).

```bash
python3.12 -m venv .venv
source .venv/bin/activate
cp -r sample_data data                                # 연습용 샘플 데이터 (선택)
python -m budget_app --help
python -m budget_app --data-dir sample_data list      # 저장 폴더 지정 (명령 앞에 써야 함)
```

`data/` 폴더는 개인 기록이 들어가므로 `.gitignore`에 등록되어 있습니다.
`sample_data/`는 GitHub에 올라가는 가짜 연습 데이터입니다.

## 저장 파일

기본 폴더는 `./data`이고 `--data-dir`로 바꿀 수 있습니다.
JSONL(한 줄 = 한 레코드)로 저장하며, 파일이나 폴더가 없으면 자동으로 만들어집니다.

| 파일 | 한 줄의 모양 |
|---|---|
| `data/transactions.jsonl` | `{"id": "TX-000001", "type": "expense", "date": "2024-01-05", "amount": 8000, "category": "food", "memo": "점심", "tags": ["meal"]}` |
| `data/categories.jsonl` | `{"name": "food"}` |
| `data/budgets.jsonl` | `{"month": "2024-01", "amount": 500000}` |

카테고리 파일이 비어 있으면 `category add`로 먼저 카테고리를 등록해야 거래를 추가할 수 있습니다.

JSONL을 고른 이유: `amount`가 숫자로, `tags`가 리스트로 그대로 저장되고 읽혀서
CSV처럼 쉼표/따옴표 문제나 타입 변환을 신경 쓰지 않아도 되기 때문입니다.

## 주요 명령

```bash
python -m budget_app add                                   # 대화형 입력 (틀리면 다시 물음)
python -m budget_app list --limit 5                        # 최신순
python -m budget_app search --category food --type expense --from 2024-01-01 --to 2024-01-31 --q 점심 --tag meal
python -m budget_app summary --month 2024-01 --top 3       # 합계, 잔액, 예산 사용률, 지출 TOP N
python -m budget_app budget set --month 2024-01 --amount 500000
python -m budget_app category list
python -m budget_app category add                          # 대화형 입력
python -m budget_app category remove                       # 사용 중인 카테고리는 삭제 거절
python -m budget_app update --id TX-000001 --amount 9000
python -m budget_app delete --id TX-000001
python -m budget_app export --out export.csv --month 2024-01
python -m budget_app import --from export.csv
```

모든 명령은 `--help`로 사용법을 볼 수 있습니다.
오류가 나면 스택트레이스 대신 `[오류] 원인 (힌트)` 한 줄을 출력하고 종료 코드 1로 끝납니다.
정상 종료는 0입니다.

### 실행 예시

```
$ python -m budget_app summary --month 2024-01 --top 3
총 수입: 100000원
총 지출: 11000원
잔액: 89000원
예산: 500000원 (사용률 2.2%)
지출 TOP 3
1) food 8000원
2) transport 3000원
```

## import/export CSV 스키마

UTF-8, 헤더 포함.

| column | required | 설명 |
|---|---|---|
| date | Y | YYYY-MM-DD |
| type | Y | income / expense |
| category | Y | 등록된 카테고리 |
| amount | Y | 양수 정수 |
| memo | N | 문자열 |
| tags | N | 쉼표(,) 구분 문자열 |

- `export`는 `--month YYYY-MM` 또는 `--from/--to` 중 하나 이상이 필수입니다.
- `import`는 한 줄씩 검증하며, 잘못된 줄은 건너뛰고(`skipped`) 나머지만 저장합니다.
  id는 CSV에 없으므로 가져올 때 새로 부여합니다.

## 구조

| 파일 | 역할 |
|---|---|
| `models.py` | 거래 한 건의 양식 (`Transaction` dataclass) |
| `storage.py` | 파일 읽기/쓰기만 담당 (`TransactionRepository`, `CategoryStore`, `BudgetStore`) |
| `services.py` | 검증과 계산 (`parse_*`, 월별 합계, 검색, 추가/삭제/수정 규칙) |
| `cli.py` | 명령 해석, 입출력, `@handle_errors` 데코레이터 |
| `__main__.py` | `python -m budget_app`의 출입구 |

흐름: `cli.py`(명령 받기) → `services.py`(검증, 판단) → `storage.py`(파일 입출력) → 결과를 다시 `cli.py`가 출력

## 설계 결정

- **update는 옵션 방식으로 고정**: `update --id <id> [--date ...] [--type ...] [--category ...] [--amount ...] [--memo ...] [--tags ...]`. 준 옵션만 바꾸고 나머지는 유지합니다.
- **스트리밍**: 거래 읽기는 제너레이터(`yield`)로 한 줄씩 처리합니다.
  `list`는 `deque(maxlen=limit)`로 최근 N개만 메모리에 두고,
  `search`는 조건에 맞은 결과만 모아서 뒤집어 최신순으로 출력합니다.
- **안전한 수정/삭제**: `update`/`delete`는 임시 파일(`.tmp`)에 쓴 뒤 `replace`로 교체합니다.
  쓰는 도중 실패해도 원본은 보존됩니다.
- **검증 먼저**: 실패할 수 있는 검사는 파일을 건드리기 전에 합니다.
  그래서 잘못된 입력은 데이터를 바꾸지 않습니다.
- **id**: 개수 + 1이 아니라 기존 id 중 최댓값 + 1입니다. 삭제 후에도 id가 겹치지 않습니다.
- **예산**: 같은 달을 다시 설정하면 마지막 값이 적용됩니다 (`budgets.jsonl`에는 기록이 쌓임).
- **카테고리 삭제**: 해당 카테고리를 쓰는 거래가 있으면 삭제를 거절합니다.
- **데코레이터**: `@handle_errors`가 `ValueError`를 받아 `[오류]` 출력과 종료 코드 1을 한 곳에서 처리합니다.
- **월 범위**: `--month 2024-01`은 `2024-01-01` ~ `2024-01-99`(문자열 비교용 값)로 바꿔 검색합니다.
  날짜가 `YYYY-MM-DD` 형식의 문자열이라 대소 비교만으로 월 경계가 맞기 때문입니다.

## 한계

- `import`는 중복 거래를 검사하지 않아 같은 CSV를 다시 가져오면 거래가 중복으로 쌓입니다.
- `import`는 줄마다 `next_id()`가 파일 전체를 읽어서 거래가 아주 많으면 느립니다.
- `--memo ""`로 메모를 지우면 빈 문자열이 아니라 `null`로 저장됩니다.
- `search`는 최신순 출력을 위해 조건에 맞은 결과를 한 번 메모리에 모읍니다.
- 한 번에 한 프로세스만 쓰는 것을 가정합니다. 동시에 실행하면 id가 겹치거나 파일이 꼬일 수 있습니다.
- 카테고리 이름을 바꾸는 기능이 없습니다.

## 배운 점

- **계층을 나누면 고칠 곳이 한 곳**입니다. 파일 입출력은 `storage`, 검증과 판단은 `services`, 입출력 화면은 `cli`에 두니
  "카테고리가 등록돼 있는지 확인" 같은 규칙을 `add`, `update`, `import`가 같이 쓸 수 있었습니다.
- **`yield`로 한 줄씩 처리**하면 파일이 커져도 메모리에 전체를 올리지 않습니다.
  `list --limit 3`처럼 필요한 만큼만 읽고 멈출 수 있다는 점이 가장 분명한 장점이었습니다.
- **타입 힌트는 실행을 막는 검사가 아니라 표지판**입니다. 실행 중에는 검사하지 않으므로
  금액이 양수인지, 날짜가 실제로 있는 날짜인지는 직접 `parse_*`로 검증해야 했습니다.
- **"동작한다"와 "맞다"는 다릅니다.** 정상 입력만 테스트하면 빈 줄, 없는 파일, 경계값(0, 1),
  `None` 값 같은 문제를 놓칩니다. 일부러 틀린 값을 넣어 보는 습관이 중요했습니다.
- **데코레이터**로 반복되던 `try/except`를 한 곳에 모으고 종료 코드까지 일관되게 처리했습니다.
  `*args, **kwargs`로 어떤 함수든 감쌀 수 있고, `return`을 빼먹으면 결과가 `None`이 된다는 것도 확인했습니다.
