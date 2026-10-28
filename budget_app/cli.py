import argparse
import sys
from collections.abc import Callable

# cli는 services만 안다. storage와 models는 import하지 않는다.
from .services import BudgetService, parse_amount, parse_date, parse_memo, parse_tags, parse_type


def handle_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            print(f"[오류] {e}")
            sys.exit(1)
        except OSError as e:
            print(f"[오류] 파일을 처리할 수 없습니다: {e} (경로와 권한을 확인하세요)")
            sys.exit(1)
        except (KeyboardInterrupt, EOFError):
            print("\n[취소] 입력을 취소했습니다.")
            sys.exit(1)
    return wrapper


def ask(prompt: str, check: Callable[[str], object]) -> str:
    """통과할 때까지 다시 묻는다. 검사만 하고, 실제 변환과 저장은 서비스가 한다."""
    while True:
        raw = input(prompt)
        try:
            check(raw)
            return raw
        except ValueError as e:
            print(f"[오류] {e}")


def format_tx(tx) -> str:
    return f"{tx.id} | {tx.date} | {tx.type} | {tx.category} | {tx.amount} | {tx.memo or ''}"


@handle_errors
def run_add(service: BudgetService, args) -> None:
    raw_date = ask("날짜(YYYY-MM-DD): ", parse_date)
    raw_type = ask("타입(income/expense): ", parse_type)
    raw_category = ask("카테고리: ", service.parse_category)
    raw_amount = ask("금액(양수): ", parse_amount)
    raw_memo = ask("메모(선택): ", parse_memo)
    raw_tags = ask("태그(쉼표로 구분, 없으면 엔터): ", parse_tags)
    tx_id = service.add_transaction(raw_date, raw_type, raw_category, raw_amount, raw_memo, raw_tags)
    print(f"[저장 완료] id={tx_id}")

@handle_errors
def run_list(service: BudgetService, args) -> None:
    for tx in service.recent(args.limit):
        print(format_tx(tx))

@handle_errors
def run_search(service: BudgetService, args) -> None:
    results = service.search(category=args.category, tx_type=args.tx_type,
                             date_from=args.date_from, date_to=args.date_to,
                             keyword=args.keyword, tag=args.tag)
    if not results:
        print("검색 결과 없음")
    for tx in results:
        print(format_tx(tx))

@handle_errors
def run_summary(service: BudgetService, args) -> None:
    summary = service.summary(args.month, args.top)
    if not summary.has_data:
        print("데이터 없음")
        return
    print(f"총 수입: {summary.total_income}원")
    print(f"총 지출: {summary.total_expense}원")
    print(f"잔액: {summary.balance}원")
    if summary.budget is None:
        print("예산: 미설정")
    else:
        print(f"예산: {summary.budget}원 (사용률 {summary.usage_percent:.1f}%)")
        if summary.over_amount > 0:
            print(f"예산보다 많은 금액을 소비하셨습니다. 초과 금액: {summary.over_amount}원")
    print(f"지출 TOP {args.top}")
    for rank, (name, amount) in enumerate(summary.top_items, start=1):
        print(f"{rank}) {name} {amount}원")

@handle_errors
def run_budget_set(service: BudgetService, args) -> None:
    month, amount = service.set_budget(args.month, args.amount)
    print(f"[저장 완료] {month} 예산 {amount}원")

@handle_errors
def run_category_list(service: BudgetService, args) -> None:
    for name in service.list_categories():
        print(f"- {name}")

@handle_errors
def run_category_add(service: BudgetService, args) -> None:
    name = service.add_category(input("카테고리명: "))
    print(f"[저장 완료] category = {name}")

@handle_errors
def run_category_remove(service: BudgetService, args) -> None:
    name = service.remove_category(input("카테고리명: "))
    print(f"[삭제 완료] category = {name}")

@handle_errors
def run_update(service: BudgetService, args) -> None:
    tx_id = service.update(args.tx_id, date=args.date, tx_type=args.tx_type,
                           category=args.category, amount=args.amount,
                           memo=args.memo, tags=args.tags)
    print(f"[수정 완료] id={tx_id}")

@handle_errors
def run_delete(service: BudgetService, args) -> None:
    tx_id = service.delete(args.tx_id)
    print(f"[삭제 완료] id={tx_id}")

@handle_errors
def run_export(service: BudgetService, args) -> None:
    count = service.export_csv(args.out, month=args.month, date_from=args.date_from, date_to=args.date_to)
    print(f"[완료] {args.out} ({count} records)")

@handle_errors
def run_import(service: BudgetService, args) -> None:
    imported, errors = service.import_csv(args.in_path)
    print(f"[완료] imported={imported}, skipped={len(errors)}")
    for line_no, reason in errors:
        print(f"  - {line_no}번째 줄 건너뜀: {reason}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="budget_app", description="용돈 기입장")
    parser.add_argument("--data-dir", default="data", help="데이터 저장 폴더 (기본값: data)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("add", help="거래 추가 (대화형)")

    category = sub.add_parser("category", help="카테고리 관리")
    category_sub = category.add_subparsers(dest="action", required=True)
    category_sub.add_parser("list", help="카테고리 목록 보기")
    category_sub.add_parser("add", help="카테고리 추가")
    category_sub.add_parser("remove", help="카테고리 삭제")

    delete_parser = sub.add_parser("delete", help="거래 삭제")
    delete_parser.add_argument("--id", dest="tx_id", required=True, help="삭제할 거래 id")

    list_parser = sub.add_parser("list", help="거래 목록")
    list_parser.add_argument("--limit", type=int, default=10, help="보여줄 개수")

    budget = sub.add_parser("budget", help="예산 관리")
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

    update_parser = sub.add_parser("update", help="거래 수정 (옵션 방식)")
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
    return parser


def main() -> None:
    # 1부: 명령 정의, 2부: 해석
    args = build_parser().parse_args()
    service = BudgetService(args.data_dir)   # cli가 만드는 건 서비스 하나뿐

    # 3부: 업무 배분
    if args.command == "category":
        if args.action == "list":
            run_category_list(service, args)
        elif args.action == "add":
            run_category_add(service, args)
        elif args.action == "remove":
            run_category_remove(service, args)
    elif args.command == "budget":
        if args.action == "set":
            run_budget_set(service, args)
    elif args.command == "add":
        run_add(service, args)
    elif args.command == "list":
        run_list(service, args)
    elif args.command == "summary":
        run_summary(service, args)
    elif args.command == "search":
        run_search(service, args)
    elif args.command == "delete":
        run_delete(service, args)
    elif args.command == "update":
        run_update(service, args)
    elif args.command == "export":
        run_export(service, args)
    elif args.command == "import":
        run_import(service, args)
