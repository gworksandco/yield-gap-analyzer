import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models.stock_record import YearlyDividendYield  # noqa: E402
from scanner.quality_filter import (  # noqa: E402
    compute_consecutive_no_cut_years,
    passes_quality_filter,
)


def test_consecutive_no_cut_years_all_increasing():
    yearly = [
        YearlyDividendYield(2021, 10.0, 1000.0, 0.01),
        YearlyDividendYield(2022, 10.0, 1000.0, 0.01),
        YearlyDividendYield(2023, 12.0, 1000.0, 0.012),
        YearlyDividendYield(2024, 12.0, 1000.0, 0.012),
        YearlyDividendYield(2025, 15.0, 1000.0, 0.015),
    ]
    # 2025>=2024, 2024>=2023, 2023>=2022, 2022>=2021 -> 4連続
    assert compute_consecutive_no_cut_years(yearly) == 4


def test_consecutive_no_cut_years_stops_at_cut():
    yearly = [
        YearlyDividendYield(2021, 10.0, 1000.0, 0.01),
        YearlyDividendYield(2022, 15.0, 1000.0, 0.015),
        YearlyDividendYield(2023, 5.0, 1000.0, 0.005),  # 減配
        YearlyDividendYield(2024, 10.0, 1000.0, 0.01),
        YearlyDividendYield(2025, 12.0, 1000.0, 0.012),
    ]
    # 2025>=2024, 2024>=2023 -> ここまでOK(2), 2023>=2022は減配なので停止
    assert compute_consecutive_no_cut_years(yearly) == 2


def test_consecutive_no_cut_years_missing_year_breaks_streak():
    yearly = [
        YearlyDividendYield(2021, 10.0, 1000.0, 0.01),
        YearlyDividendYield(2022, 0.0, None, 0.0, is_missing=True),
        YearlyDividendYield(2023, 10.0, 1000.0, 0.01),
        YearlyDividendYield(2024, 12.0, 1000.0, 0.012),
        YearlyDividendYield(2025, 15.0, 1000.0, 0.015),
    ]
    # 2025>=2024, 2024>=2023 -> 2, 2023>=2022は2022がmissingなので停止
    assert compute_consecutive_no_cut_years(yearly) == 2


def test_passes_quality_filter_none_values_not_excluded():
    assert passes_quality_filter(
        market_cap=None,
        equity_ratio=None,
        consecutive_no_cut_years=0,
        min_market_cap=1e10,
        min_equity_ratio=40,
        min_consecutive_no_cut_years=0,
    ) is True


def test_passes_quality_filter_rejects_below_threshold():
    assert passes_quality_filter(
        market_cap=1e9,
        equity_ratio=50,
        consecutive_no_cut_years=5,
        min_market_cap=1e10,
        min_equity_ratio=40,
        min_consecutive_no_cut_years=0,
    ) is False
