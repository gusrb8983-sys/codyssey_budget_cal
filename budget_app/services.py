import csv
from pathlib import Path
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

def remove_category(category_store: CategoryStore, repo: TransactionRepository, name: str) -> str:
    name = name.strip()
    names = category_store.list_all()
    if name == "":
        raise ValueError("이름이 비어있습니다. 다시 입력해주세요.")
    elif name not in names:          # 검사 2: 목록에 없으면
        raise ValueError(f"등록되지 않은 카테고리입니다: {name}")
    elif is_category_used(repo, name):          # 검사 3: 거래에서 사용 중이면 (is_category_used 사용)
        raise ValueError(f"사용 중인 카테고리라 삭제할 수 없습니다: {name} (해당 거래를 먼저 수정하거나 삭제하세요)")
    else:
         category_store.remove(name)           # 저장: 관리인에게 지우라고 시키기
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

def is_category_used(repo: TransactionRepository, name: str) -> bool:
    for tx in repo.iter_all():
        if tx.category == name:
            return True
    return False

def delete_transaction(repo: TransactionRepository, raw_id: str) -> str:
    tx_id = raw_id.strip()
    if tx_id == '':
        raise ValueError("아이디를 입력해주십시오.")
    elif not repo.delete(tx_id):
        raise ValueError("존재하지 않는 id입니다.")
    return tx_id

def update_transaction(repo, category_store, raw_id, date=None, tx_type=None,
                       category=None, amount=None, memo=None, tags=None) -> str:
    tx_id = raw_id.strip()
    if not tx_id:
        raise ValueError("아이디를 입력해주십시오")
    changes = {}
    if date is not None:
        changes["date"] = parse_date(date)
    if tx_type is not None:
        changes["type"] = parse_type(tx_type)    
    if category is not None:
        changes["category"] = parse_category(category_store, category)
    if amount is not None:
        changes["amount"] = parse_amount(amount)
    if memo is not None:
        changes["memo"] = parse_memo(memo)
    if tags is not None:
        changes["tags"] = parse_tags(tags)
    if not changes:
        raise ValueError("바꿀 항목을 하나 이상 지정하세요 (예: --amount 5000)")
    if not repo.update(tx_id, changes):
        raise ValueError("존재하지 않는 id입니다.")
    return tx_id

def export_transactions(repo, out_path, month=None, date_from=None, date_to=None) -> int:
    if month is None and date_from is None and date_to is None:
        raise ValueError("--month 또는 --from/--to 중 하나는 필요합니다") # 1. month, date_from, date_to가 전부 None이면 → raise ValueError("--month 또는 --from/--to 중 하나는 필요합니다")
    if month:
        tx_month = parse_month(month)
        date_from = f"{tx_month}-01"
        date_to = f"{tx_month}-99" 
    rows = search_transactions(repo, date_from=date_from, date_to=date_to)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "type", "category", "amount", "memo", "tags"])
        count = 0                      # for보다 위, 딱 한 번 (with 안쪽 맨 앞 또는 with 위)
        for tx in rows:                # 매번
            writer.writerow([tx.date, tx.type, tx.category, tx.amount, tx.memo or "", ",".join(tx.tags) if tx.tags else ""])
            count = count + 1          # 매번
    return count                       # 반복이 끝난 뒤 한 번 (with 바깥)

def import_transactions(repo, category_store, in_path) -> tuple[int, int]:
    if not Path(in_path).exists():
        raise ValueError(f"파일을 찾을 수 없습니다: {in_path} (경로를 확인하세요)")
    imported = 0
    skipped = 0
    with open(in_path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            try:
                tx_date = parse_date(row["date"])
                tx_type = parse_type(row["type"])        # row["type"]을 parse_type에
                tx_category = parse_category(category_store, row["category"])
                tx_amount = parse_amount(row["amount"])      # row["amount"]를 parse_amount에
                tx_memo = parse_memo(row["memo"])        # row["memo"]를 parse_memo에
                tx_tags = parse_tags(row["tags"])        # row["tags"]를 parse_tags에
                transaction = Transaction(id=repo.next_id(), type=tx_type, date=tx_date,
                                          amount=tx_amount, category=tx_category,
                                          memo=tx_memo, tags=tx_tags)
                repo.append(transaction)
                imported += 1
            except ValueError:
                skipped += 1
    return imported, skipped