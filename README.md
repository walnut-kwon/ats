# Hanta

개인 리서치용 자동 매매 신호 실험 프로젝트입니다.

초기 목표는 실거래 자동화가 아니라, OHLCV 데이터를 기반으로 기술적 지표를 계산하고
각 지표를 정량적인 매수/매도 신호로 변환한 뒤 백테스트로 검증하는 것입니다.

## MVP

첫 번째 개발 범위는 다음으로 제한합니다.

- 입력: `date`, `open`, `high`, `low`, `close`, `volume`
- 지표: 이동평균, MA Slope, RSI, MACD, ATR, Bollinger Bands, OBV, 캔들 비율
- 정규화: rolling z-score, min-max scaling, robust scaling
- 출력: 지표별 `-1.0 ~ +1.0` 신호와 최종 `-100 ~ +100` 점수
- 검증: CSV 샘플 데이터 기반 단위 테스트와 간단한 백테스트

뉴스 감성, 거시경제, 실시간 주문, 포트폴리오 리밸런싱은 이후 단계에서 다룹니다.

## Project Layout

```text
hanta/
  docs/
    architecture.md
    mvp.md
    roadmap.md
  data/
    sample/
  notebooks/
  src/
    hanta/
      data.py
      indicators.py
      scalers.py
      signals.py
      scoring.py
      backtest.py
  tests/
```

## Setup

`uv` 사용을 권장합니다.

```bash
uv sync
uv run pytest
```

패키지를 직접 실행할 때는 다음처럼 시작합니다.

```bash
uv run hanta --help
```

샘플 CSV를 전체 파이프라인으로 분석하려면 다음을 실행합니다.

```bash
uv run hanta analyze data/sample/sample_ohlcv.csv --tail 5
```

기본 출력은 `date`, `close`, 최종 `score`, 그룹별 `score_*`, 주요 `signal_*` 컬럼만 보여주는 요약입니다.
전체 지표와 신호 컬럼을 터미널에 출력하려면 `--full`을 사용합니다.

```bash
uv run hanta analyze data/sample/sample_ohlcv.csv --tail 5 --full
```

분석 결과 전체를 CSV로 저장하려면 `--output`을 사용합니다.

```bash
uv run hanta analyze data/sample/sample_ohlcv.csv --output data/sample/analysis.csv
```

기본 long-only 백테스트를 실행하려면 다음을 사용합니다.

```bash
uv run hanta backtest data/sample/sample_ohlcv.csv --tail 5
```

## Development Direction

1. CSV 로더와 OHLCV 컬럼 검증을 안정화합니다.
2. 지표 계산 함수를 하나씩 추가합니다.
3. 각 지표를 공통 신호 스케일인 `-1.0 ~ +1.0`로 변환합니다.
4. 가중합 점수로 `-100 ~ +100` 최종 신호를 만듭니다.
5. 과거 데이터로 신호와 수익률의 관계를 검증합니다.
