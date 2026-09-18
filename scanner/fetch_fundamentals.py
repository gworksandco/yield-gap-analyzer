"""
優良株フィルタに必要な財務指標をyfinanceから取得するモジュール。

取得項目:
- market_cap: 時価総額
- equity_ratio: 自己資本比率（%） = 純資産 / 総資産 * 100
- per, pbr: 参考指標
- consecutive_no_cut_years の算出に使う年次配当系列は fetch_dividends 側の
  yearly_yields（dividend_per_share）から計算する（このモジュールでは扱わない）
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import yfinance as yf

from scanner.fetch_dividends import _retry_call, _sleep_with_jitter  # レート制限対策を再利用

logger = logging.getLogger(__name__)


@dataclass
class FundamentalsResult:
    ticker: str
    market_cap: Optional[float]
    equity_ratio: Optional[float]
    per: Optional[float]
    pbr: Optional[float]
    fetch_ok: bool
    error: Optional[str] = None


def fetch_fundamentals(ticker: str) -> FundamentalsResult:
    try:
        tk = yf.Ticker(ticker)
        info = _retry_call(lambda: tk.get_info())

        market_cap = info.get("marketCap")
        per = info.get("trailingPE")
        pbr = info.get("priceToBook")

        equity_ratio = _compute_equity_ratio(tk)

        return FundamentalsResult(
            ticker=ticker,
            market_cap=float(market_cap) if market_cap else None,
            equity_ratio=equity_ratio,
            per=float(per) if per else None,
            pbr=float(pbr) if pbr else None,
            fetch_ok=True,
        )
    except Exception as exc:
        logger.error("failed to fetch fundamentals for %s: %s", ticker, exc)
        return FundamentalsResult(
            ticker=ticker,
            market_cap=None,
            equity_ratio=None,
            per=None,
            pbr=None,
            fetch_ok=False,
            error=str(exc),
        )
    finally:
        _sleep_with_jitter()


def _compute_equity_ratio(tk: yf.Ticker) -> Optional[float]:
    """balance_sheetから自己資本比率(%) = 純資産合計 / 資産合計 * 100 を計算する。

    yfinanceのbalance_sheetは行名が銘柄・時期によって揺れることがあるため、
    候補となる行名を順に探す。取得できない場合はNoneを返す（フィルタ側で
    「データなし」として扱う）。
    """
    try:
        bs = _retry_call(lambda: tk.balance_sheet)
        if bs is None or bs.empty:
            return None

        latest_col = bs.columns[0]

        total_assets = _first_matching_row(
            bs, latest_col, ["Total Assets"]
        )
        total_equity = _first_matching_row(
            bs,
            latest_col,
            [
                "Stockholders Equity",
                "Total Equity Gross Minority Interest",
                "Common Stock Equity",
            ],
        )

        if total_assets is None or total_equity is None or total_assets == 0:
            return None

        return float(total_equity) / float(total_assets) * 100
    except Exception as exc:
        logger.warning("equity ratio computation failed: %s", exc)
        return None


def _first_matching_row(df, col, candidate_row_names: list[str]) -> Optional[float]:
    for name in candidate_row_names:
        if name in df.index:
            value = df.loc[name, col]
            if value is not None and not (isinstance(value, float) and value != value):  # NaN check
                return float(value)
    return None
