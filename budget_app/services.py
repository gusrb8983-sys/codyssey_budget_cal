from collections.abc import Iterator
from .storage import CategoryStore
from datetime import datetime
from collections import deque
from .storage import TransactionRepository
from .models import Transaction

def add_category(store: CategoryStore, name: str) -> str:
    name = name.strip()
    names = store.list_all()
    if name == "":
        raise ValueError("이름이 비어있습니다. 다시 입력해주세요.")
    elif name in names:
        raise ValueError(f"이미 등록된 카테고리입니다: {name}")
    else:
        store.add(name)
    return name

def parse_type(raw: str) -> str:
    value = raw.strip() # 1. 앞뒤 공백 정리
    if not (value == "income" or value == "expense"): 
        raise ValueError("income 혹은 expense 중에서 선택해주십시오.") # 2. income도 expense도 아니면 → raise ValueError("...")
    return value # 3. 정리된 값 돌려주기


def parse_amount(raw: str) -> int:
    raw_amount = raw.strip() # 1. 앞뒤 공백 정리
    if not raw_amount.isdigit():
        raise ValueError("금액은 1 이상의 정수여야 합니다. (예: 15000)") # 2. 정수로 바꿀 수 없는 글자면 → raise ValueError("...")
    amount = int(raw_amount) # 3. 숫자로 바꾸기
    if amount <= 0:
        raise ValueError("금액은 1 이상의 정수여야 합니다. (예: 150000)") # 4. 0 이하면 → raise ValueError("...")
    return amount # 5. 숫자 돌려주기

def parse_month(raw: str) -> str:
    raw_month = raw.strip()
    try:
        datetime.strptime(raw_month, "%Y-%m")
    except ValueError:
        raise ValueError("날짜 형식을 올바르게 설정해주세요. (예: 2024-10)") from None
    return raw_month

def parse_date(raw: str) -> str:
    raw_date = raw.strip()
    try:
        datetime.strptime(raw_date, "%Y-%m-%d")
    except ValueError:
        raise ValueError("날짜 형식을 올바르게 설정해주세요. (예: 2024-10-03)") from None
    return raw_date

def parse_category(store: CategoryStore, raw: str) -> str:
    category = raw.strip()
    categories = store.list_all()
    if category not in categories:
        raise ValueError("카테고리 목록에 등록되어 있지 않습니다. category add로 먼저 등록해주세요.")
    return category

def parse_memo(raw: str) -> str | None:
    memo = raw.strip()
    if memo == "":
        return None
    else:
        return memo

def parse_tags(raw: str) -> list[str] | None:
    raw_tags = raw.strip()
    if raw_tags == "":
        return None
    tags = raw_tags.split(",")
    tag_list = []
    for tag in tags:
        new_tag = tag.strip()
        if not new_tag == "":
            tag_list.append(new_tag)
    if tag_list == []:
        return None
    else:
        return tag_list

def recent_transactions(repo: TransactionRepository, limit: int) -> list[Transaction]:
    if limit < 1:
        raise ValueError("--limit은 1 이상의 정수여야 합니다(예: --limit 5)")
    else:
        box = deque(maxlen=limit)                  # 1. deque(maxlen=limit) 바구니 준비
        for tx in repo.iter_all():
            box.append(tx)                         # 2. repo.iter_all()를 for로 돌면서 바구니에 append
        return list(reversed(box))                 # 3. 바구니를 뒤집어서 리스트로 돌려주기 

def monthly_totals(repo: TransactionRepository, month: str) -> tuple[int, int, dict[str, int]]:
    total_income = 0
    total_expense = 0
    category_totals = {} # 1. 바구니 세 개 준비 (total_income = 0, total_expense = 0, category_totals = {})
    for tx in repo.iter_all(): # 2. repo.iter_all()를 for로 돌면서
        if not tx.date.startswith(month):
            continue        #    - 이 거래가 해당 월이 아니면 continue
        else:                   
            if tx.type == "income":
                total_income = total_income + tx.amount
            else:
                total_expense = total_expense + tx.amount
                category_totals[tx.category] = category_totals.get(tx.category, 0) + tx.amount   #    - 위의 분기대로 더하기 
    return total_income, total_expense, category_totals # 3. return total_income, total_expense, category_totals

def top_categories(category_totals: dict[str, int], top: int) -> list[tuple[str, int]]:
    if top < 1:
        raise ValueError("--top은 1 이상의 정수여야 합니다 (예: --top 3)")
    else:
        return sorted(category_totals.items(), key=lambda pair: pair[1], reverse=True)[:top]

def search_transactions(repo, category=None, tx_type=None, date_from=None, date_to=None, keyword=None, tag=None):
    for tx in repo.iter_all():
        if category is not None and tx.category != category:
            continue
        if tx_type is not None and tx.type != tx_type:
            continue
        if date_from is not None and tx.date < date_from:
            continue
        if date_to is not None and tx.date > date_to:
            continue
        if keyword is not None and (tx.memo is None or keyword not in tx.memo):
            continue
        if tag is not None and (tx.tags is None or tag not in tx.tags):
            continue
        yield tx