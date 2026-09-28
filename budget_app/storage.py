from .models import Transaction
from dataclasses import asdict
import json

def iter_transactions(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip() == "":
                continue
            data = json.loads(line)
            tx = Transaction(**data)
            yield tx

def append_transaction(path, tx):
    with open(path, "a", encoding="utf-8") as f:
        data = asdict(tx)
        line = json.dumps(data, ensure_ascii=False)
        f.write(line + "\n")