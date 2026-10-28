from collections import deque
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

from .models import MonthlySummary, Transaction
from .storage import BudgetStore, CategoryStore, CsvFile, TransactionRepository

# import/export CSV 스키마 (미션이 고정한 규칙이라 services에 둔다)
CSV_HEADER = ["date", "type", "category", "amount", "memo", "tags"]


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

def search_transactions(repo: TransactionRepository, category: str | None = None, tx_type: str | None = None, date_from: str | None = None, date_to: str | None = None, keyword: str | None = None, tag: str | None = None) -> Iterator[Transaction]:
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

def update_transaction(repo: TransactionRepository, category_store: CategoryStore, raw_id: str, date: str | None = None, tx_type: str | None = None,
                       category: str | None = None, amount: str | None = None, memo: str | None = None, tags: str | None = None) -> str:
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

def to_csv_rows(transactions: Iterator[Transaction]) -> Iterator[list]:
    """거래를 한 건씩 CSV 한 줄(리스트)로 바꿔서 흘려보낸다."""
    for tx in transactions:
        tags = ",".join(tx.tags) if tx.tags else ""
        yield [tx.date, tx.type, tx.category, tx.amount, tx.memo or "", tags]

def export_transactions(repo: TransactionRepository, out_path: str, month: str | None = None, date_from: str | None = None, date_to: str | None = None) -> int:
    if month is None and date_from is None and date_to is None:
        raise ValueError("--month 또는 --from/--to 중 하나는 필요합니다")
    if month:
        tx_month = parse_month(month)
        date_from = f"{tx_month}-01"
        date_to = f"{tx_month}-99"
    else:
        if date_from is not None:
            date_from = parse_date(date_from)
        if date_to is not None:
            date_to = parse_date(date_to)
    rows = search_transactions(repo, date_from=date_from, date_to=date_to)
    return CsvFile(out_path).write(CSV_HEADER, to_csv_rows(rows))   # 파일 쓰기는 storage(CsvFile)에 맡긴다

def import_transactions(repo: TransactionRepository, category_store: CategoryStore, in_path: str) -> tuple[int, list[tuple[int, str]]]:
    csv_file = CsvFile(in_path)
    if not csv_file.exists():
        raise ValueError(f"파일을 찾을 수 없습니다: {in_path} (경로를 확인하세요)")
    header = csv_file.read_header()
    missing = []
    for column in CSV_HEADER:
        if column not in header:
            missing.append(column)
    if missing:
        raise ValueError(f"CSV 헤더에 필요한 열이 없습니다: {', '.join(missing)} (첫 줄은 {','.join(CSV_HEADER)} 이어야 합니다)")

    next_number = int(repo.next_id().split("-")[1])   # 번호는 처음에 한 번만 구하고 1씩 올린다 (줄마다 파일 전체를 읽지 않게)
    imported = 0
    errors = []                                       # 건너뛴 줄의 (줄 번호, 사유) 리포트
    for line_no, row in enumerate(csv_file.iter_rows(), start=2):   # 1번 줄은 헤더
        try:
            tx_date = parse_date(row["date"] or "")
            tx_type = parse_type(row["type"] or "")
            tx_category = parse_category(category_store, row["category"] or "")
            tx_amount = parse_amount(row["amount"] or "")
            tx_memo = parse_memo(row["memo"] or "")
            tx_tags = parse_tags(row["tags"] or "")
        except ValueError as e:
            errors.append((line_no, str(e)))
            continue
        transaction = Transaction(id=f"TX-{next_number:06d}", type=tx_type, date=tx_date,
                                  amount=tx_amount, category=tx_category,
                                  memo=tx_memo, tags=tx_tags)
        repo.append(transaction)
        next_number = next_number + 1
        imported = imported + 1
    return imported, errors


class BudgetService:
    """cli가 유일하게 의존하는 창구. 저장소(storage)를 안에서 만들고, cli 대신 연결한다."""

    def __init__(self, data_dir: str) -> None:
        base = Path(data_dir)
        self.repo = TransactionRepository(str(base / "transactions.jsonl"))
        self.categories = CategoryStore(str(base / "categories.jsonl"))
        self.budgets = BudgetStore(str(base / "budgets.jsonl"))

    # --- 카테고리 ---
    def list_categories(self) -> list[str]:
        return self.categories.list_all()

    def add_category(self, raw_name: str) -> str:
        return add_category(self.categories, raw_name)

    def remove_category(self, raw_name: str) -> str:
        return remove_category(self.categories, self.repo, raw_name)

    def parse_category(self, raw: str) -> str:
        return parse_category(self.categories, raw)

    # --- 거래 ---
    def add_transaction(self, raw_date: str, raw_type: str, raw_category: str,
                        raw_amount: str, raw_memo: str, raw_tags: str) -> str:
        # 검증을 전부 먼저 하고, 통과하면 그때 번호를 매겨 저장한다
        tx_date = parse_date(raw_date)
        tx_type = parse_type(raw_type)
        tx_category = self.parse_category(raw_category)
        tx_amount = parse_amount(raw_amount)
        tx_memo = parse_memo(raw_memo)
        tx_tags = parse_tags(raw_tags)
        transaction = Transaction(id=self.repo.next_id(), type=tx_type, date=tx_date,
                                  amount=tx_amount, category=tx_category,
                                  memo=tx_memo, tags=tx_tags)
        self.repo.append(transaction)
        return transaction.id

    def recent(self, limit: int) -> list[Transaction]:
        return recent_transactions(self.repo, limit)

    def search(self, category: str | None = None, tx_type: str | None = None, date_from: str | None = None,
               date_to: str | None = None, keyword: str | None = None, tag: str | None = None) -> list[Transaction]:
        if date_from is not None:
            date_from = parse_date(date_from)
        if date_to is not None:
            date_to = parse_date(date_to)
        results = list(search_transactions(self.repo, category=category, tx_type=tx_type,
                                           date_from=date_from, date_to=date_to,
                                           keyword=keyword, tag=tag))
        results.reverse()          # 파일은 오래된 순이라 뒤집어서 최신순으로
        return results

    def update(self, raw_id: str, date: str | None = None, tx_type: str | None = None, category: str | None = None,
               amount: str | None = None, memo: str | None = None, tags: str | None = None) -> str:
        return update_transaction(self.repo, self.categories, raw_id, date=date, tx_type=tx_type,
                                  category=category, amount=amount, memo=memo, tags=tags)

    def delete(self, raw_id: str) -> str:
        return delete_transaction(self.repo, raw_id)

    # --- 예산과 요약 ---
    def set_budget(self, raw_month: str, raw_amount: str) -> tuple[str, int]:
        month = parse_month(raw_month)
        amount = parse_amount(raw_amount)
        self.budgets.set(month, amount)
        return month, amount

    def summary(self, raw_month: str, top: int) -> MonthlySummary:
        month = parse_month(raw_month)
        total_income, total_expense, category_totals = monthly_totals(self.repo, month)
        top_items = top_categories(category_totals, top)
        return MonthlySummary(month=month, total_income=total_income, total_expense=total_expense,
                              top_items=top_items, budget=self.budgets.get(month))

    # --- CSV ---
    def export_csv(self, out_path: str, month: str | None = None,
                   date_from: str | None = None, date_to: str | None = None) -> int:
        return export_transactions(self.repo, out_path, month=month, date_from=date_from, date_to=date_to)

    def import_csv(self, in_path: str) -> tuple[int, list[tuple[int, str]]]:
        return import_transactions(self.repo, self.categories, in_path)
