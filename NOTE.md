uv run pytest          # 테스트 실행
uv run ruff check .    # 코드 스타일 검사
uv add pandas numpy    # 일반 의존성 추가
uv add --dev pytest    # 개발용 의존성 추가
uv run python          # 프로젝트 환경의 Python 실행