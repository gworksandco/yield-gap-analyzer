"""
JPX（東京証券取引所）全銘柄のティッカーリストを取得するモジュール。

ネットキャッシュ版と同じ方針: JPXが公開している上場銘柄一覧（Excel/CSV）を
取得し、yfinance用のティッカー形式（例: "7203.T"）に変換する。

JPXの公開URLはページ改訂で変わることがあるため、URLは定数化して差し替えやすくする。
"""

from __future__ import annotations

import io
import logging

import pandas as pd
import requests

logger = logging.getLogger(__name__)

# JPX「東証上場銘柄一覧」のダウンロードURL（要: 最新URLへの追従）
# 注: このファイルは月次更新（毎月第3営業日に前月末時点データを掲載）。
#     日次バッチで毎回取得しても実質は月1回しか更新されない点に留意。
JPX_LISTED_ISSUES_URL = (
    "https://www.jpx.co.jp/markets/statistics-equities/misc/tvdivq0000001vg2-att/data_j.xlsx"
)

# 対象とする市場区分（プライム・スタンダード・グロース）。ETF/REIT等は除外する。
TARGET_MARKET_SEGMENTS = [
    "プライム（内国株式）",
    "スタンダード（内国株式）",
    "グロース（内国株式）",
]


def fetch_jpx_universe() -> pd.DataFrame:
    """JPX公式の上場銘柄一覧を取得し、対象市場区分の銘柄のみに絞ったDataFrameを返す。

    戻り値の列: ticker（例 "7203.T"）, code（例 "7203"）, company_name, market_segment
    """
    resp = requests.get(JPX_LISTED_ISSUES_URL, timeout=30)
    resp.raise_for_status()

    df = pd.read_excel(io.BytesIO(resp.content))

    # JPXのExcel列名は変更されることがあるため、想定と異なる場合はここでエラーを出す
    expected_cols = {"コード", "銘柄名", "市場・商品区分"}
    if not expected_cols.issubset(set(df.columns)):
        raise ValueError(
            f"Unexpected JPX file columns: {list(df.columns)} — "
            f"expected at least {expected_cols}"
        )

    df = df[df["市場・商品区分"].isin(TARGET_MARKET_SEGMENTS)].copy()

    df["code"] = df["コード"].astype(str).str.strip()
    df["ticker"] = df["code"] + ".T"
    df["company_name"] = df["銘柄名"].astype(str).str.strip()
    df["market_segment"] = df["市場・商品区分"]

    result = df[["ticker", "code", "company_name", "market_segment"]].reset_index(drop=True)
    logger.info("fetched %d tickers from JPX universe", len(result))
    return result
