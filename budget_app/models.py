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