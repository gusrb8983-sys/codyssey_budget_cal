from dataclasses import dataclass


@dataclass
class Transaction:
    id: str
    type: str
    date: str
    amount: int
    category: str
    memo: str | None = None
    tags: list[str] | None = None


@dataclass
class MonthlySummary:
    """한 달 요약 결과. 계산은 services가 하고, cli는 이 값을 출력만 한다."""
    month: str
    total_income: int
    total_expense: int
    top_items: list[tuple[str, int]]
    budget: int | None = None

    @property
    def balance(self) -> int:
        return self.total_income - self.total_expense

    @property
    def has_data(self) -> bool:
        return self.total_income != 0 or self.total_expense != 0

    @property
    def usage_percent(self) -> float | None:
        if self.budget is None:
            return None
        return self.total_expense / self.budget * 100

    @property
    def over_amount(self) -> int:
        if self.budget is None or self.total_expense <= self.budget:
            return 0
        return self.total_expense - self.budget
