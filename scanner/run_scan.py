"""
全銘柄スキャンのエントリポイント。GitHub Actionsから日次実行される想定。

処理フロー:
1. JPX全銘柄リストを取得
2. 各銘柄について配当履歴・財務指標を取得
3. StockRecordを組み立ててCSVに書き出す（data/results.csv）

Streamlit側はこのCSVを読むだけで計算は行わない（ネットキャッシュ版と同じ構成）。
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date
from pathlib import Path

import pandas as pd

# プロジェクトルートをパスに追加（GitHub Actionsからの実行を想定）
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models.stock_record import StockRecord  # noqa: E402
from scanner.fetch_dividends import (  # noqa: E402
    fetch_dividend_yields,
    compute_current_and_avg_yield,
)
from scanner.fetch_fundamentals import fetch_fundamentals  # noqa: E402
from scanner.quality_filter import compute_consecutive_no_cut_years  # noqa: E402
from scanner.universe import fetch_jpx_universe  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "results.csv"


def scan_single_stock(ticker: str, company_name: str) -> StockRecord | None:
    div_result = fetch_dividend_yields(ticker)
    if not div_result.fetch_ok:
        logger.warning("skipping %s: dividend fetch failed (%s)", ticker, div_result.error)
        return None

    current_yield, avg_yield_5y = compute_current_and_avg_yield(div_result)
    yield_gap_ratio = StockRecord.compute_yield_gap_ratio(current_yield, avg_yield_5y)

    fundamentals = fetch_fundamentals(ticker)
    consecutive_no_cut_years = compute_consecutive_no_cut_years(div_result.extended_dividend_years)

    data_quality_flag = None
    if not fundamentals.fetch_ok:
        data_quality_flag = "fundamentals_fetch_failed"
    if yield_gap_ratio is None:
        data_quality_flag = (
            f"{data_quality_flag},no_dividend_history"
            if data_quality_flag
            else "no_dividend_history"
        )

    return StockRecord(
        ticker=ticker,
        company_name=company_name,
        current_yield=current_yield,
        avg_yield_5y=avg_yield_5y,
        yield_gap_ratio=yield_gap_ratio if yield_gap_ratio is not None else 0.0,
        yearly_yields=div_result.yearly_yields,
        market_cap=fundamentals.market_cap,
        equity_ratio=fundamentals.equity_ratio,
        consecutive_no_cut_years=consecutive_no_cut_years,
        per=fundamentals.per,
        pbr=fundamentals.pbr,
        last_updated=date.today(),
        data_quality_flag=data_quality_flag,
    )


def run_scan(limit: int | None = None, output_path: Path = DEFAULT_OUTPUT_PATH) -> None:
    universe = fetch_jpx_universe()
    if limit:
        universe = universe.head(limit)

    records: list[dict] = []
    total = len(universe)

    for i, row in enumerate(universe.itertuples(index=False), start=1):
        logger.info("[%d/%d] scanning %s (%s)", i, total, row.ticker, row.company_name)
        record = scan_single_stock(row.ticker, row.company_name)
        if record is not None:
            records.append(record.to_flat_dict())

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    logger.info("wrote %d records to %s", len(df), output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Yield-Gap Analyzer 全銘柄スキャン")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="動作確認用に対象銘柄数を制限する（本番実行では指定しない）",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="出力CSVパス",
    )
    args = parser.parse_args()
    run_scan(limit=args.limit, output_path=args.output)


if __name__ == "__main__":
    main()
