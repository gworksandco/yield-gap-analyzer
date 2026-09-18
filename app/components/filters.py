"""
サイドバーのフィルタUI。

buy_signalの判定はここで動的に行う（合意事項3: CSVには生の乖離率のみ持たせ、
閾値判定はUI側のスライダーで行う設計）。
"""

from __future__ import annotations

import pandas as pd
import streamlit as st


def render_filters() -> dict:
    """サイドバーにフィルタスライダーを表示し、選択された閾値をdictで返す。"""
    st.sidebar.header("フィルタ条件")

    min_yield_gap_ratio_pct = st.sidebar.slider(
        "利回り乖離率の下限（買いサイン判定）",
        min_value=0,
        max_value=200,
        value=50,
        step=5,
        format="%d%%",
        help="現在の配当利回りが、過去5年平均よりどれだけ割安（高利回り）になっているかを示します。値が大きいほど「今が買い時」の可能性が高い銘柄です。",
    )
    min_yield_gap_ratio = min_yield_gap_ratio_pct / 100

    min_current_yield_pct = st.sidebar.slider(
        "現在利回りの下限",
        min_value=0.0,
        max_value=10.0,
        value=3.0,
        step=0.1,
        format="%.1f%%",
        help="現在の予想（実績）配当利回りがこの値以上の銘柄のみ表示する",
    )
    min_current_yield = min_current_yield_pct / 100

    st.sidebar.subheader("優良株フィルタ")

    min_market_cap_oku = st.sidebar.number_input(
        "時価総額 下限（億円）",
        min_value=0,
        value=500,
        step=50,
    )

    min_equity_ratio = st.sidebar.slider(
        "自己資本比率 下限（%）",
        min_value=0,
        max_value=100,
        value=40,
        step=5,
    )

    min_consecutive_no_cut_years = st.sidebar.slider(
        "連続非減配年数 下限",
        min_value=0,
        max_value=10,
        value=5,
        step=1,
    )

    max_per = st.sidebar.number_input(
        "PER 上限（0=フィルタなし）",
        min_value=0.0,
        value=0.0,
        step=1.0,
    )

    max_pbr = st.sidebar.number_input(
        "PBR 上限（0=フィルタなし）",
        min_value=0.0,
        value=0.0,
        step=0.1,
    )

    max_payout_ratio = st.sidebar.number_input(
        "配当性向 上限（%）（0=フィルタなし）",
        min_value=0.0,
        value=0.0,
        step=5.0,
        help="利益に対して配当に回している割合。高すぎる銘柄（無理をして配当を出している可能性）を除外できます。データなしの銘柄は除外しません。",
    )

    return {
        "min_yield_gap_ratio": min_yield_gap_ratio,
        "min_current_yield": min_current_yield,
        "min_market_cap": min_market_cap_oku * 1e8,
        "min_equity_ratio": min_equity_ratio,
        "min_consecutive_no_cut_years": min_consecutive_no_cut_years,
        "max_per": max_per if max_per > 0 else None,
        "max_pbr": max_pbr if max_pbr > 0 else None,
        "max_payout_ratio": max_payout_ratio if max_payout_ratio > 0 else None,
    }


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """dfに対して優良株フィルタを適用し、buy_signal列を付与して返す。

    データ欠損（NaN）の銘柄は該当フィルタで除外しない（判定不能として通す）方針。
    """
    out = df.copy()

    mask = pd.Series(True, index=out.index)

    if "current_yield" in out.columns:
        mask &= out["current_yield"] >= filters["min_current_yield"]

    if "market_cap" in out.columns:
        mask &= out["market_cap"].isna() | (out["market_cap"] >= filters["min_market_cap"])

    if "equity_ratio" in out.columns:
        mask &= out["equity_ratio"].isna() | (out["equity_ratio"] >= filters["min_equity_ratio"])

    if "consecutive_no_cut_years" in out.columns:
        mask &= out["consecutive_no_cut_years"] >= filters["min_consecutive_no_cut_years"]

    if filters.get("max_per") and "per" in out.columns:
        mask &= out["per"].isna() | (out["per"] <= filters["max_per"])

    if filters.get("max_pbr") and "pbr" in out.columns:
        mask &= out["pbr"].isna() | (out["pbr"] <= filters["max_pbr"])

    if filters.get("max_payout_ratio") and "payout_ratio" in out.columns:
        mask &= out["payout_ratio"].isna() | (out["payout_ratio"] <= filters["max_payout_ratio"])

    out = out[mask].copy()

    out["buy_signal"] = out["yield_gap_ratio"] >= filters["min_yield_gap_ratio"]

    return out
