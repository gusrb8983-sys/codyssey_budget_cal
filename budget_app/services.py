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

def parse_type(raw: str) -> str:
    value = raw.strip() # 1. 앞뒤 공백 정리
    if not (value == "income" or value == "expense"): 
        raise ValueError("income 혹은 expense 중에서 선택해주십시오.") # 2. income도 expense도 아니면 → raise ValueError("...")
    return value # 3. 정리된 값 돌려주기


def parse_amount(raw: str) -> int:
    raw_amount = raw.strip() # 1. 앞뒤 공백 정리
    if not raw_amount.isdigit():
        raise ValueError("금액은 1 이상의 정수여야 합니다. (예: 15000)") # 2. 정수로 바꿀 수 없는 글자면 → raise ValueError("...")
    amount = int(raw_amount) # 3. 숫자로 바꾸기
    if amount <= 0:
        raise ValueError("금액은 1 이상의 정수여야 합니다. (예: 150000)") # 4. 0 이하면 → raise ValueError("...")
    return amount # 5. 숫자 돌려주기