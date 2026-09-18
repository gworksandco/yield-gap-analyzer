"""
yfinanceから配当履歴・株価履歴を取得し、年度ごとの「実績配当 ÷ 株価」を計算するモジュール。

設計方針（合意済み）:
- 利回りは「直近期実績配当 ÷ 現在株価」で統一算式にする（予想利回りdividendYieldは使わない）
- 過去5年分も同じ算式（その年の実績配当 ÷ その年の参照株価）で揃える
- 配当が取得できない/無配の年は yield_value=0.0 として平均計算に含める（除外しない）

レート制限対策:
ネットキャッシュ版（全銘柄yfiananceスキャン）で有効だった方針を踏襲:
- リトライ+指数バックオフ
- 銘柄間にリクエスト間隔を空ける
- 同時実行数を絞る
"""

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass
from datetime import date
from typing import Optional

import pandas as pd
import yfinance as yf

from models.stock_record import YearlyDividendYield

logger = logging.getLogger(__name__)

# --- レート制限対策のパラメータ ---
MAX_RETRIES = 4
BASE_BACKOFF_SECONDS = 2.0
REQUEST_INTERVAL_SECONDS = 0.3  # 銘柄間の最低待機時間（+ジッター）
JITTER_SECONDS = 0.2

NUM_YEARS = 5


@dataclass
class DividendFetchResult:
    ticker: str
    current_price: Optional[float]
    current_year_dividend: Optional[float]  # 直近期の実績配当（1株あたり）
    yearly_yields: list[YearlyDividendYield]
    fetch_ok: bool
    error: Optional[str] = None


def _sleep_with_jitter() -> None:
    time.sleep(REQUEST_INTERVAL_SECONDS + random.uniform(0, JITTER_SECONDS))


def _retry_call(fn, *args, **kwargs):
    """一時的なエラー（レート制限など）に対してバックオフしながらリトライする。"""
    last_exc = None
    for attempt in range(MAX_RETRIES):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:  # yfinance側の例外型は不安定なため広めに捕捉
            last_exc = exc
            wait = BASE_BACKOFF_SECONDS * (2**attempt) + random.uniform(0, 1.0)
            logger.warning(
                "fetch failed (attempt %d/%d): %s — retrying in %.1fs",
                attempt + 1,
                MAX_RETRIES,
                exc,
                wait,
            )
            time.sleep(wait)
    raise last_exc


def _annual_dividends_from_history(dividends: pd.Series) -> dict[int, float]:
    """yfinanceのTicker.dividends（日次配当額のSeries）を会計年度合計に集計する。

    注: 簡易的に暦年（1〜12月）で集計する。日本企業の決算期に厳密に合わせる場合は
    別途、決算期情報を使ったリサンプリングに差し替える。
    """
    if dividends is None or dividends.empty:
        return {}
    by_year = dividends.groupby(dividends.index.year).sum()
    return {int(year): float(amount) for year, amount in by_year.items()}


def _price_for_year(history: pd.DataFrame, year: int) -> Optional[float]:
    """指定年の年末終値（直近取引日）を参照株価として返す。取得できなければNone。"""
    if history is None or history.empty:
        return None
    year_data = history[history.index.year == year]
    if year_data.empty:
        return None
    return float(year_data["Close"].iloc[-1])


def fetch_dividend_yields(ticker: str, num_years: int = NUM_YEARS) -> DividendFetchResult:
    """指定銘柄について、直近利回りと過去num_years年分の年次利回りを取得する。"""
    try:
        tk = yf.Ticker(ticker)

        dividends = _retry_call(lambda: tk.dividends)
        # 十分な長さの価格履歴（配当計算の年末終値取得のため）
        history = _retry_call(lambda: tk.history, period=f"{num_years + 1}y", interval="1d")

        info = _retry_call(lambda: tk.fast_info)
        current_price = float(info.get("lastPrice")) if info and info.get("lastPrice") else None

        annual_div = _annual_dividends_from_history(dividends)

        this_year = date.today().year
        # 直近「確定済み」年度 = 前年（当年はまだ配当が確定していない可能性が高いため）
        latest_complete_year = this_year - 1

        target_years = list(range(latest_complete_year - num_years + 1, latest_complete_year + 1))

        yearly_yields: list[YearlyDividendYield] = []
        for fy in target_years:
            div = annual_div.get(fy, 0.0)
            price = _price_for_year(history, fy)

            if div <= 0 or price is None or price <= 0:
                yearly_yields.append(
                    YearlyDividendYield(
                        fiscal_year=fy,
                        dividend_per_share=div,
                        reference_price=price,
                        yield_value=0.0,
                        is_missing=True,
                    )
                )
            else:
                yearly_yields.append(
                    YearlyDividendYield(
                        fiscal_year=fy,
                        dividend_per_share=div,
                        reference_price=price,
                        yield_value=div / price,
                        is_missing=False,
                    )
                )

        current_year_dividend = annual_div.get(latest_complete_year, 0.0)

        return DividendFetchResult(
            ticker=ticker,
            current_price=current_price,
            current_year_dividend=current_year_dividend,
            yearly_yields=yearly_yields,
            fetch_ok=True,
        )
    except Exception as exc:
        logger.error("failed to fetch dividend data for %s: %s", ticker, exc)
        return DividendFetchResult(
            ticker=ticker,
            current_price=None,
            current_year_dividend=None,
            yearly_yields=[],
            fetch_ok=False,
            error=str(exc),
        )
    finally:
        _sleep_with_jitter()


def compute_current_and_avg_yield(
    result: DividendFetchResult,
) -> tuple[float, float]:
    """current_yield（直近実績配当÷現在株価）とavg_yield_5y（欠損年=0を含む単純平均）を返す。

    現在株価が取得できない場合、current_yieldは0.0として扱う（呼び出し側でdata_quality_flag等に
    反映することを想定）。
    """
    if result.current_price and result.current_year_dividend is not None and result.current_price > 0:
        current_yield = result.current_year_dividend / result.current_price
    else:
        current_yield = 0.0

    if not result.yearly_yields:
        avg_yield_5y = 0.0
    else:
        avg_yield_5y = sum(y.yield_value for y in result.yearly_yields) / len(result.yearly_yields)

    return current_yield, avg_yield_5y
