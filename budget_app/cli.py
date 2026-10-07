import argparse

from .storage import CategoryStore


def main() -> None:
    # 1부: 은행 세우기
    parser = argparse.ArgumentParser(prog="budget_app", description="용돈 기입장")
    sub = parser.add_subparsers(dest="command", required=True)

    category = sub.add_parser("category", help="카테고리 관리")
    category_sub = category.add_subparsers(dest="action", required=True)
    category_sub.add_parser("list", help="카테고리 목록 보기")

    # 2부: 손님 받기
    args = parser.parse_args()

    # 3부: 업무 처리
    if args.command == "category":
        if args.action == "list":
            store = CategoryStore("data/categories.jsonl")
            names = store.list_all()
            for name in names:
                print(f"- {name}")