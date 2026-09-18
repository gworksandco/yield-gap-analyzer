import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models.stock_record import StockRecord, YearlyDividendYield  # noqa: E402
from scanner.fetch_dividends import DividendFetchResult, compute_current_and_avg_yield  # noqa: E402


def test_yield_gap_ratio_basic():
    # current=4%, avg=2% -> gap = 4/2 - 1 = 1.0 (100%)
    assert StockRecord.compute_yield_gap_ratio(0.04, 0.02) == 1.0


def test_yield_gap_ratio_zero_average_returns_none():
    assert StockRecord.compute_yield_gap_ratio(0.03, 0.0) is None


def test_avg_yield_includes_missing_years_as_zero():
    yearly = [
        YearlyDividendYield(2021, 10.0, 1000.0, 0.01, is_missing=False),
        YearlyDividendYield(2022, 0.0, None, 0.0, is_missing=True),  # 無配年
        YearlyDividendYield(2023, 10.0, 1000.0, 0.01, is_missing=False),
        YearlyDividendYield(2024, 10.0, 1000.0, 0.01, is_missing=False),
        YearlyDividendYield(2025, 10.0, 1000.0, 0.01, is_missing=False),
    ]
    result = DividendFetchResult(
        ticker="TEST.T",
        current_price=1000.0,
        current_year_dividend=10.0,
        yearly_yields=yearly,
        fetch_ok=True,
    )
    current_yield, avg_yield_5y = compute_current_and_avg_yield(result)
    assert current_yield == 0.01
    # (0.01+0+0.01+0.01+0.01)/5 = 0.008
    assert abs(avg_yield_5y - 0.008) < 1e-9


def test_current_yield_zero_when_price_missing():
    result = DividendFetchResult(
        ticker="TEST.T",
        current_price=None,
        current_year_dividend=10.0,
        yearly_yields=[],
        fetch_ok=True,
    )
    current_yield, avg_yield_5y = compute_current_and_avg_yield(result)
    assert current_yield == 0.0
    assert avg_yield_5y == 0.0
