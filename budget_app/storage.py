from .models import Transaction
import json

def iter_transactions(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            tx = Transaction(**data)
            yield tx