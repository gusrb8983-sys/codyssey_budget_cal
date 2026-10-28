import sys

# 3.10 미만이면 다른 모듈을 불러오기 전에 친절하게 멈춘다 (str | None 문법 때문에 3.10 이상 필요)
if sys.version_info < (3, 10):
    print(f"[오류] Python 3.10 이상이 필요합니다 (현재 {sys.version.split()[0]}). "
          "가상환경을 켰는지 확인하세요: source .venv/bin/activate")
    sys.exit(1)

from .cli import main  # noqa: E402

main()
