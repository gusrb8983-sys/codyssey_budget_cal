from .storage import CategoryStore


def add_category(store: CategoryStore, name: str) -> str:
    name = name.strip()
    names = store.list_all()
    if name == "":
        raise ValueError("이름이 비어있습니다. 다시 입력해주세요.")
    elif name in names:
        raise ValueError("이미 등록된 카테고리입니다: {name}")
    else:
        store.add(name)
    return name