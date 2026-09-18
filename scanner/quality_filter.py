"""
優良株フィルタ用のロジック。

- 連続非減配年数の算出（配当履歴から）
- 時価総額・自己資本比率などの閾値判定はStreamlit側スライダーで動的に行うため、
  ここでは「フィルタに使う生データを揃える」ところまでを担当する
  （合意事項3: buy_signal相当の閾値判定はapp側に置く設計と一貫させる）
"""

from __future__ import annotations

from models.stock_record import YearlyDividendYield


def compute_consecutive_no_cut_years(yearly_yields: list[YearlyDividendYield]) -> int:
    """年次配当データ（古い年→新しい年の順を想定）から、直近まで遡って
    「前年以上の配当を維持した」連続年数を計算する。

    ルール:
    - 直近年からさかのぼり、dividend_per_share が前年以上であれば「非減配」として継続年数+1
    - 前年よりdividend_per_shareが減っていたら、そこで連続記録が途切れる
    - 配当データが欠損（is_missing=True）の年は「減配」とみなし、そこで連続記録が途切れる
      （データが無い=非減配と楽観視しない）
    - 配当データが2年未満しかない場合は 0 を返す（判定不能）
    """
    if len(yearly_yields) < 2:
        return 0

    # fiscal_year昇順に並び替え（古い→新しい）
    sorted_years = sorted(yearly_yields, key=lambda y: y.fiscal_year)

    consecutive = 0
    # 新しい年から一つ前の年と比較していく
    for i in range(len(sorted_years) - 1, 0, -1):
        current = sorted_years[i]
        previous = sorted_years[i - 1]

        if current.is_missing or previous.is_missing:
            break

        if current.dividend_per_share >= previous.dividend_per_share:
            consecutive += 1
        else:
            break

    return consecutive


def passes_quality_filter(
    *,
    market_cap: float | None,
    equity_ratio: float | None,
    consecutive_no_cut_years: int,
    min_market_cap: float,
    min_equity_ratio: float,
    min_consecutive_no_cut_years: int,
) -> bool:
    """スキャン結果CSVに含める前の一次フィルタ（バッチ側での足切り用、任意）。

    Streamlit側でも同じ条件をスライダーで再適用できるようにするため、
    ここでの閾値は「明らかに対象外」を除外する緩めの一次フィルタとしての利用を想定。
    データ欠損（None）の場合は「判定不能」として除外はしない（Falseにしない）。
    """
    if market_cap is not None and market_cap < min_market_cap:
        return False
    if equity_ratio is not None and equity_ratio < min_equity_ratio:
        return False
    if consecutive_no_cut_years < min_consecutive_no_cut_years:
        return False
    return True
