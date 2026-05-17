# MVP Scope

이 문서는 첫 구현 범위를 작게 유지하기 위한 기준입니다.

## Goal

CSV 형태의 OHLCV 데이터를 입력하면 다음 결과를 얻습니다.

- 기술적 지표가 추가된 데이터프레임
- 지표별 매수/매도 신호
- 최종 종합 점수
- 간단한 백테스트 결과

## Input Contract

필수 컬럼은 다음과 같습니다.

| Column | Type | Description |
| --- | --- | --- |
| `date` | date-like | 거래일 |
| `open` | float | 시가 |
| `high` | float | 고가 |
| `low` | float | 저가 |
| `close` | float | 종가 |
| `volume` | float | 거래량 |

## Indicator Set

초기 구현 지표는 다음으로 제한합니다.

| Category | Indicators |
| --- | --- |
| Trend | SMA, EMA, MA Slope |
| Momentum | RSI, MACD |
| Volatility | ATR, Bollinger Bands |
| Volume | OBV |
| Candle | Body Ratio, Upper Shadow Ratio, Lower Shadow Ratio |

## Data Length And Warm-Up

지표는 계산 가능한 최소 데이터 길이와 신호로 신뢰할 수 있는 데이터 길이가 다릅니다.

EMA는 최신 데이터에 더 큰 가중치를 주지만, 이론적으로는 과거 데이터가 지수적으로 작아지는 꼬리 형태로 계속 반영됩니다. 따라서 `EMA 60`은 60거래일 이후부터 계산할 수 있지만, 초기값의 영향이 충분히 줄어든 뒤 신호로 사용하는 편이 안전합니다.

RSI는 두 가지 계산 방식을 둡니다. 기본값인 Wilder RSI는 상승폭과 하락폭을 `alpha = 1 / window`로 smoothing하므로 EMA와 비슷한 warm-up 이슈가 있습니다. 비교용 Simple RSI는 최근 window 안의 상승폭/하락폭만 단순평균으로 계산합니다.

MACD는 기본값으로 `12, 26, 9`를 사용합니다. 이는 최적값이라기보다 널리 쓰이는 기준선이며, 이후 백테스트에서 `6, 13, 5`처럼 더 민감한 조합이나 `19, 39, 9`처럼 더 느린 조합과 비교합니다.

ATR은 True Range를 기반으로 하며 기본값은 Wilder 방식의 `ATR 14`입니다. 비교를 위해 Simple ATR도 지원합니다.

Bollinger Bands는 기본값으로 `window = 20`, `multiplier = 2.0`을 사용합니다. 표준편차는 최근 window 내부 데이터를 현재 구간의 모집단으로 보고 `ddof = 0`으로 계산합니다.

OBV는 종가가 전일보다 상승하면 거래량을 더하고, 하락하면 거래량을 빼며, 동일하면 유지합니다. 첫 행은 이전 종가가 없으므로 `0`에서 시작합니다.

캔들 비율은 단일 봉의 몸통과 위/아래 꼬리를 `high - low` 범위 대비 비율로 표현합니다. `high == low`인 봉은 분모가 0이므로 비율을 `NaN`으로 둡니다.

초기 기준은 다음처럼 둡니다.

| Indicator | Minimum Rows | Preferred Warm-Up |
| --- | ---: | ---: |
| `EMA 5` | 5 | 15 |
| `EMA 20` | 20 | 60 |
| `EMA 60` | 60 | 180 |
| `RSI 14 (Wilder)` | 14 | 42 |
| `RSI 14 (Simple)` | 14 | 14 |
| `MACD 12-26-9` | 34 | 78 |
| `ATR 14 (Wilder)` | 14 | 42 |
| `ATR 14 (Simple)` | 14 | 14 |
| `Bollinger Bands 20-2` | 20 | 20 |
| `OBV` | 1 | 1 |
| `Candle Ratios` | 1 | 1 |

백테스트에 필요한 데이터 길이는 대략 다음 기준으로 잡습니다.

```text
longest indicator window * 3 + evaluation period
```

예를 들어 `EMA 60`을 쓰고 최근 1년, 약 252거래일을 평가하려면 최소 약 432거래일의 데이터가 필요합니다.

시장 변동성이 큰 구간에서는 긴 warm-up이 과거 레짐을 과도하게 반영할 수 있으므로, 이 값은 고정 규칙이 아니라 보수적인 기본값으로 둡니다. 이후 백테스트에서 `span * 2`, `span * 3`, `span * 4`를 비교해 조정합니다.

## Signal Contract

모든 지표 신호는 공통 범위로 변환합니다.

| Value | Meaning |
| --- | --- |
| `1.0` | 강한 매수 |
| `0.5` | 약한 매수 |
| `0.0` | 중립 |
| `-0.5` | 약한 매도 |
| `-1.0` | 강한 매도 |

최종 점수는 개별 `signal_*` 컬럼 가중합으로 계산한 뒤 `-100 ~ +100` 범위로 클리핑합니다. 값이 `NaN`인 신호는 해당 행에서 제외하고, 사용 가능한 신호 가중치만으로 재정규화합니다.

초기 개별 신호 가중치는 다음과 같습니다.

| Signal | Weight |
| --- | ---: |
| `signal_ma_alignment_5_20_60` | 0.15 |
| `signal_ma_slope_5` | 0.08 |
| `signal_ma_slope_20` | 0.12 |
| `signal_ma_slope_60` | 0.10 |
| `signal_rsi_14` | 0.18 |
| `signal_macd_histogram_12_26_9` | 0.17 |
| `signal_atr_expansion_14` | 0.08 |
| `signal_bb_percent_b_20_2` | 0.07 |
| `signal_obv_change` | 0.05 |

초기 신호 변환 규칙은 다음과 같습니다.

| Source | Signal Rule |
| --- | --- |
| `ma_slope_*` | rolling z-score를 `2.0`으로 나눈 뒤 `-1 ~ +1` 클리핑 |
| `sma_5`, `sma_20`, `sma_60` | pairwise alignment로 `signal_ma_alignment_5_20_60` 생성 |
| `rsi_*` | `(RSI - 50) / 50` 후 클리핑 |
| `macd_histogram_*` | rolling z-score를 `2.0`으로 나눈 뒤 클리핑 |
| `atr_14` | 최근 ATR 평균 대비 확장 비율을 `0 ~ +1`로 변환 |
| `bb_percent_b_*` | `(percent_b - 0.5) / 0.5` 후 클리핑 |
| `obv` | OBV 1기간 변화량의 rolling robust score를 `2.0`으로 나눈 뒤 클리핑 |

캔들 비율은 아직 직접 신호화하지 않습니다. 단일 캔들 모양은 맥락 의존성이 커서, 추세/변동성/거래량 신호와 함께 별도 패턴 규칙으로 다룹니다.

## Out Of Scope

다음 항목은 MVP 이후로 미룹니다.

- 증권사 API 연동
- 실시간 자동 주문
- 뉴스 감성 분석
- 거시경제 지표 반영
- DTW 기반 차트 패턴 매칭
- 일목균형표와 매물대 분석
- 다종목 포트폴리오 최적화
