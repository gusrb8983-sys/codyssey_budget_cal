import json
from collections.abc import Iterator
from dataclasses import asdict

from .models import Transaction

class TransactionRepository:
    def __init__(self, path: str) -> None:
        self.path = path

    def iter_all(self: str) -> Iterator[Transaction]:
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