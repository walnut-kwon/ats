# Architecture

프로젝트는 데이터 처리 파이프라인을 작은 단계로 나누어 구성합니다.

```text
OHLCV data
  -> indicators
  -> scalers
  -> signals
  -> scoring
  -> backtest/report
```

## Modules

### `ats.data`

CSV, Parquet 등 외부 데이터를 읽고 OHLCV 컬럼 계약을 검증합니다.

### `ats.indicators`

원시 가격과 거래량을 기반으로 기술적 지표 컬럼을 추가합니다.
이 모듈은 판단을 내리지 않고 계산만 담당합니다.

### `ats.scalers`

서로 다른 단위의 값을 비교 가능한 스케일로 변환합니다.
이 모듈은 매수/매도 판단을 하지 않고 다음과 같은 수학적 변환만 제공합니다.

- fixed min-max scaling
- centered min-max scaling
- rolling z-score
- rolling robust score based on median and IQR
- clipping
- tanh squashing

### `ats.signals`

지표 값을 매수/매도 방향과 강도로 변환합니다.
모든 신호는 `-1.0 ~ +1.0` 범위를 따릅니다.

### `ats.scoring`

지표별 신호에 가중치를 적용해 최종 점수를 계산합니다.
최종 점수는 `-100 ~ +100` 범위를 따릅니다.

### `ats.backtest`

신호가 미래 수익률과 어떤 관계를 갖는지 확인하는 최소 백테스트를 제공합니다.
초기에는 체결, 수수료, 슬리피지 모델을 단순하게 둡니다.

## Design Rules

- 지표 계산과 신호 판단은 분리합니다.
- 지표 함수는 입력 데이터프레임을 직접 변경하지 않고 복사본을 반환합니다.
- 각 단계의 입력/출력 컬럼 이름은 문서화합니다.
- 매매 주문 API는 검증된 신호 모델 이후에 추가합니다.
