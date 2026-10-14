import argparse

from .models import Transaction
from .storage import CategoryStore, TransactionRepository
from .services import (
    add_category, parse_amount, parse_category,
    parse_date, parse_memo, parse_tags, parse_type,
    recent_transactions,
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
            for recent_tx in recent_transactions(repo, args.limit):
                print(f"{recent_tx.id} | {recent_tx.date} | {recent_tx.type} | {recent_tx.category} | {recent_tx.amount} | {recent_tx.memo or ''}")
        except ValueError as e:
            print(f"[오류] {e}")