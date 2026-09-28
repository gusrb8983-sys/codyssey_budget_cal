import json
from collections.abc import Iterator
from dataclasses import asdict

from .models import Transaction

def iter_transactions(path: str) -> Iterator[Transaction]:
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip() == "":
                continue
            data = json.loads(line)
            tx = Transaction(**data)
            yield tx

def append_transaction(path: str, tx: Transaction) -> None:
    with open(path, "a", encoding="utf-8") as f:
        data = asdict(tx)
        line = json.dumps(data, ensure_ascii=False)
        f.write(line + "\n")