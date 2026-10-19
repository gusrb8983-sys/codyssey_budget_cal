import argparse

from .models import Transaction
from .storage import CategoryStore, TransactionRepository, BudgetStore
from .services import (
    add_category, parse_amount, monthly_totals, parse_category,
    parse_date, parse_memo, parse_month, parse_tags, parse_type,
    recent_transactions, top_categories, search_transactions
)

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
    
    # 2부: 손님 받기
    args = parser.parse_args()

    # 3부: 업무 처리
    if args.command == "category":
        if args.action == "list":
            store = CategoryStore("data/categories.jsonl")
            names = store.list_all()
            for name in names:
                print(f"- {name}")
        elif args.action == "add":
            store = CategoryStore("data/categories.jsonl")
            try:
                raw_name = input("카테고리명: ")
                name = add_category(store, raw_name)
                print(f"[저장 완료] category = {name}")
            except ValueError as e:
                print(f"[오류] {e}")

    elif args.command == "add":
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

    elif args.command == "list":
        repo = TransactionRepository("data/transactions.jsonl")
        try:
            recent = recent_transactions(repo, args.limit)
        except ValueError as e:
            print(f"[오류] {e}")
        else:
            for recent_tx in recent:
                print(f"{recent_tx.id} | {recent_tx.date} | {recent_tx.type} | {recent_tx.category} | {recent_tx.amount} | {recent_tx.memo or ''}")

    elif args.command == "budget":
        if args.action == "set":
            store = BudgetStore("data/budgets.jsonl")
            try:
                month = parse_month(args.month)
                amount = parse_amount(args.amount)
                store.set(month, amount)
                print(f"[저장 완료] {month} 예산 {amount}원")
            except ValueError as e:
                print(f"[오류] {e}")

    elif args.command == "summary":
        repo = TransactionRepository("data/transactions.jsonl")
        budget_store = BudgetStore("data/budgets.jsonl")
        try:
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

        except ValueError as e:
            print(f"[오류] {e}")

    elif args.command == "search":
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