"""
1銘柄分のスキャン結果を表すデータモデル。

設計方針:
- current_yield / avg_yield_5y は「実績配当 ÷ その期の株価」で統一算式にする
  （yfinanceの予想利回り dividendYield は使わない。全銘柄一括スキャンだと
  更新タイミングのズレでデータ品質にムラが出るため）
- 配当欠損年（無配・データなし）は 0 として平均計算に含める
  （除外するとサンプル数が銘柄ごとにバラつき、乖離率の意味が不安定になるため）
- buy_signal はここでは持たない。CSVには生の乖離率と質フィルタ用の生データだけを
  持たせ、閾値判定はStreamlit側のスライダーで動的に行う設計とする
"""

from dataclasses import dataclass, field, asdict
from datetime import date
from typing import Optional


@dataclass
class YearlyDividendYield:
    """ある1年分の「実績配当 ÷ その年の株価」の記録。"""

    fiscal_year: int  # 例: 2021, 2022, ...
    dividend_per_share: float  # その期の実績配当（1株あたり、円）
    reference_price: Optional[float]  # 算式に使う株価（例: 期末終値）
    yield_value: float  # dividend_per_share / reference_price（データなし年は0.0）
    is_missing: bool = False  # 配当・株価データが取得できずyield_value=0とした年か


@dataclass
class StockRecord:
    """スキャン結果CSVの1行に対応するレコード。"""

    # --- 識別情報 ---
    ticker: str  # 例: "7203.T"
    company_name: str

    # --- 利回り乖離率のコア指標 ---
    current_yield: float  # 直近期実績配当 ÷ 現在株価
    avg_yield_5y: float  # 過去5年分（欠損年は0として含む）の単純平均
    yield_gap_ratio: float  # (current_yield / avg_yield_5y) - 1
    yearly_yields: list[YearlyDividendYield] = field(default_factory=list)  # 内訳（過去5年）

    # --- 優良株フィルタ用の生データ ---
    market_cap: Optional[float] = None  # 時価総額（円）
    equity_ratio: Optional[float] = None  # 自己資本比率（%）
    consecutive_no_cut_years: int = 0  # 連続非減配年数
    per: Optional[float] = None
    pbr: Optional[float] = None

    # --- メタ情報 ---
    last_updated: date = field(default_factory=date.today)
    data_quality_flag: Optional[str] = None  # 例: "missing_dividend_history" など注記用

    @staticmethod
    def compute_yield_gap_ratio(current_yield: float, avg_yield_5y: float) -> Optional[float]:
        """avg_yield_5yが0（全年無配）の場合は計算不能としてNoneを返す。"""
        if avg_yield_5y == 0:
            return None
        return (current_yield / avg_yield_5y) - 1

    def to_flat_dict(self) -> dict:
        """CSV書き出し用にネストを展開したdictを返す。"""
        d = asdict(self)
        d.pop("yearly_yields", None)
        for i, yy in enumerate(self.yearly_yields, start=1):
            d[f"y{i}_fiscal_year"] = yy.fiscal_year
            d[f"y{i}_dividend_per_share"] = yy.dividend_per_share
            d[f"y{i}_yield"] = yy.yield_value
            d[f"y{i}_is_missing"] = yy.is_missing
        return d
