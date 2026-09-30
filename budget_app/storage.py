import json
from collections.abc import Iterator
from dataclasses import asdict
from pathlib import Path

from .models import Transaction

class TransactionRepository:
    def __init__(self, path: str) -> None:
        self.path = path

    def iter_all(self) -> Iterator[Transaction]:
        if not Path(self.path).exists():
            return
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                if line.strip() == "":
                    continue
                data = json.loads(line)
                tx = Transaction(**data)
                yield tx

    def append(self, tx: Transaction) -> None:
        with open(self.path, "a", encoding="utf-8") as f:
            data = asdict(tx)
            line = json.dumps(data, ensure_ascii=False)
            f.write(line + "\n")

class CategoryStore:
    def __init__(self, path: str) -> None:
        self.path = path

    def list_all(self) -> list[str]:
        names = []
        if not Path(self.path).exists():
            return names
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                if line.strip() == "":
                    continue
                data = json.loads(line)
                names.append(data["name"])
            return names

    def add(self, name: str) -> None:
        with open(self.path, "a", encoding="utf-8") as f:
            data = {"name": name}
            line = json.dumps(data, ensure_ascii=False)
            f.write(line + "\n")

class BudgetStore:
    def __init__(self, path: str) -> None:
        self.path = path

    def load_all(self) -> dict[str, int]:
        budgets = {}
        if not Path(self.path).exists():
            return budgets
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                if line.strip() == "":
                    continue
                data = json.loads(line)
                budgets[data["month"]] = data["amount"]
            return budgets

    def set(self, month: str, amount: int) -> None:
        with open(self.path, "a", encoding="utf-8") as f:
            data = {"month":month, "amount": amount}
            line = json.dumps(data, ensure_ascii=False)
            f.write(line + "\n")

    def get(self, month: str) -> int | None:
        budgets = self.load_all()
        return budgets.get(month)