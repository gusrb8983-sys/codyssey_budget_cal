import argparse
import sys

from .models import Transaction
from .storage import CategoryStore, TransactionRepository, BudgetStore
from .services import (
    add_category, parse_amount, monthly_totals, parse_category,
    parse_date, parse_memo, parse_month, parse_tags, parse_type,
    recent_transactions, top_categories, search_transactions,
    remove_category, delete_transaction, update_transaction,
    export_transactions, import_transactions,
)

def handle_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            print(f"[오류] {e}")
            sys.exit(1)
    return wrapper

@handle_errors
def run_delete(args):
    repo = TransactionRepository("data/transactions.jsonl")
    tx_id = delete_transaction(repo, args.tx_id)
    print(f"[삭제 완료] id={tx_id}")

@handle_errors
def run_update(args):
    repo = TransactionRepository("data/transactions.jsonl")
    category_store = CategoryStore("data/categories.jsonl")
    tx_id = update_transaction(repo, category_store, args.tx_id,
                               date=args.date, tx_type=args.tx_type,
                               category=args.category, amount=args.amount,
                               memo=args.memo, tags=args.tags)
    print(f"[수정 완료] id={tx_id}")

@handle_errors
def run_import(args):
    repo = TransactionRepository("data/transactions.jsonl")
    category_store = CategoryStore("data/categories.jsonl")
    imported, skipped = import_transactions(repo, category_store, args.in_path)
    print(f"[완료] imported={imported}, skipped={skipped}")

@handle_errors
def run_export(args):
    repo = TransactionRepository("data/transactions.jsonl")
    count = export_transactions(repo, args.out, month=args.month, date_from=args.date_from, date_to=args.date_to)
    print(f"[완료] {args.out} ({count} records)")

@handle_errors
def run_list(args):
    repo = TransactionRepository("data/transactions.jsonl")
    recent = recent_transactions(repo, args.limit)
    for recent_tx in recent:
        print(f"{recent_tx.id} | {recent_tx.date} | {recent_tx.type} | {recent_tx.category} | {recent_tx.amount} | {recent_tx.memo or ''}")

@handle_errors
def run_budget_set(args):
    store = BudgetStore("data/budgets.jsonl")
    month = parse_month(args.month)
    amount = parse_amount(args.amount)
    store.set(month, amount)
    print(f"[저장 완료] {month} 예산 {amount}원")

@handle_errors
def run_summary(args):
    repo = TransactionRepository("data/transactions.jsonl")
    budget_store = BudgetStore("data/budgets.jsonl")
    month = parse_month(args.month)
    total_income, total_expense, category_totals = monthly_totals(repo, month)
    top_items = top_categories(category_totals, args.top)
    budget = budget_store.get(month)
    if total_income == 0 and total_expense == 0:
        print("데이터 없음")
    else:
        print(f"총 수입: {total_income}원")
        print(f"총 지출: {total_expense}원")
        print(f"잔액: {total_income - total_expense}원")
        if budget is None:
            print("예산: 미설정")
        else:
            usage = total_expense / budget * 100
            print(f"예산: {budget}원 (사용률 {usage:.1f}%)")
            if total_expense > budget:
                print(f"예산보다 많은 금액을 소비하셨습니다. 초과 금액: {total_expense - budget}")
            print(f"지출 TOP {args.top}")
            for rank, (name, amount) in enumerate(top_items, start = 1):
                print(f"{rank}) {name} {amount}원")

@handle_errors
def run_category_add(args):
    store = CategoryStore("data/categories.jsonl")
    raw_name = input("카테고리명: ")
    name = add_category(store, raw_name)
    print(f"[저장 완료] category = {name}")

@handle_errors
def run_category_remove(args):
    repo = TransactionRepository("data/transactions.jsonl")
    store = CategoryStore("data/categories.jsonl")
    raw_name = input("카테고리명: ")
    name = remove_category(store, repo, raw_name)
    print(f"[삭제 완료] category = {name}")

@handle_errors
def run_add(args):
    category_store = CategoryStore("data/categories.jsonl")
    repo = TransactionRepository("data/transactions.jsonl")
    tx_date = ask("날짜(YYYY-MM-DD): ", parse_date)
    tx_type = ask("타입(income/expense): ", parse_type)
    tx_category = ask("카테고리: ", lambda raw: parse_category(category_store, raw))
    tx_amount = ask("금액(양수): ", parse_amount)
    tx_memo = ask("메모(선택): ", parse_memo)
    tx_tags = ask("태그(쉼표로 구분, 없으면 엔터): ", parse_tags)
    transaction = Transaction(id=repo.next_id(), type=tx_type, date=tx_date, amount=tx_amount, category=tx_category, memo=tx_memo, tags=tx_tags)
    repo.append(transaction)
    print(f"[저장 완료] id={transaction.id}")

@handle_errors
def run_search(args):
    repo = TransactionRepository("data/transactions.jsonl")
    results = list(search_transactions(repo, category=args.category,
    tx_type=args.tx_type, date_from=args.date_from,
    date_to=args.date_to, keyword=args.keyword, tag=args.tag,
    ))
    if not results:
        print("검색 결과 없음")
    else:
        for tx in reversed(results):
            print(f"{tx.id} | {tx.date} | {tx.type} | {tx.category} | {tx.amount} | {tx.memo or ''}")

@handle_errors
def run_category_list(args):
    store = CategoryStore("data/categories.jsonl")
    for name in store.list_all():
        print(f"- {name}")

def ask(prompt: str, parse) -> ...:
    while True:
        raw = input(prompt)
        try:
            return parse(raw)
        except ValueError as e:
            print(f"[오류] {e}")

def main() -> None:
    # 1부: 은행 세우기
    parser = argparse.ArgumentParser(prog="budget_app", description="용돈 기입장")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("add", help="거래 추가")
    category = sub.add_parser("category", help="카테고리 관리")
    category_sub = category.add_subparsers(dest="action", required=True)
    category_sub.add_parser("list", help="카테고리 목록 보기")
    category_sub.add_parser("add", help="카테고리 추가")
    category_sub.add_parser("remove", help="카테고리 삭제")
    delete_parser = sub.add_parser("delete", help="거래 삭제")
    delete_parser.add_argument("--id", dest="tx_id", required=True, help="삭제할 거래 id")
    list_parser = sub.add_parser("list", help="거래 목록")
    list_parser.add_argument("--limit", type=int, default=10, help="보여줄 개수")
    budget = sub.add_parser("budget", help="예산 목록")
    budget_sub = budget.add_subparsers(dest="action", required=True)
    set_parser = budget_sub.add_parser("set", help="예산 설정")
    set_parser.add_argument("--month", required=True, help="예산 월 (YYYY-MM)")
    set_parser.add_argument("--amount", required=True, help="월 예산 금액 (양수 정수)")
    summary_parser = sub.add_parser("summary", help="월별 요약")
    summary_parser.add_argument("--month", required=True, help="요약할 월 (YYYY-MM)")
    summary_parser.add_argument("--top", type=int, default=3, help="지출 TOP N")
    search_parser = sub.add_parser("search", help="거래 검색")
    search_parser.add_argument("--from", dest="date_from", help="시작 날짜 (YYYY-MM-DD)")
    search_parser.add_argument("--to", dest="date_to", help="종료 날짜 (YYYY-MM-DD)")
    search_parser.add_argument("--category", help="카테고리")
    search_parser.add_argument("--type", dest="tx_type", help="income 또는 expense")
    search_parser.add_argument("--q", dest="keyword", help="메모 검색어")
    search_parser.add_argument("--tag", help="태그")
    update_parser = sub.add_parser("update", help="거래 수정")
    update_parser.add_argument("--id", dest="tx_id", required=True, help="수정할 거래 id")
    update_parser.add_argument("--date", help="날짜 (YYYY-MM-DD)")
    update_parser.add_argument("--type", dest="tx_type", help="income 또는 expense")
    update_parser.add_argument("--category", help="카테고리")
    update_parser.add_argument("--amount", help="금액 (양수 정수)")
    update_parser.add_argument("--memo", help="메모")
    update_parser.add_argument("--tags", help="태그 (쉼표로 구분)")
    export_parser = sub.add_parser("export", help="거래 CSV 내보내기")
    export_parser.add_argument("--out", required=True, help="저장할 CSV 파일 경로")
    export_parser.add_argument("--month", help="내보낼 월 (YYYY-MM)")
    export_parser.add_argument("--from", dest="date_from", help="시작 날짜 (YYYY-MM-DD)")
    export_parser.add_argument("--to", dest="date_to", help="종료 날짜 (YYYY-MM-DD)")
    import_parser = sub.add_parser("import", help="CSV 가져오기")
    import_parser.add_argument("--from", dest="in_path", required=True, help="가져올 CSV 파일 경로")

    # 2부: 손님 받기
    args = parser.parse_args()

    # 3부: 업무 처리
    if args.command == "category":
        if args.action == "list":
            run_category_list(args)
        elif args.action == "add":
            run_category_add(args)
        elif args.action == "remove":
            run_category_remove(args)

    elif args.command == "add":
        run_add(args)

    elif args.command == "list":
        run_list(args)

    elif args.command == "budget":
        if args.action == "set":
            run_budget_set(args)

    elif args.command == "summary":
        run_summary(args)

    elif args.command == "search":
        run_search(args)

    elif args.command == "delete":
        run_delete(args)

    elif args.command == "update":
        run_update(args)

    elif args.command == "export":
        run_export(args)

    elif args.command == "import":
        run_import(args)