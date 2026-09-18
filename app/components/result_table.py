"""乖離率順にソートし、買いサインをハイライトする結果テーブル表示。"""

from __future__ import annotations

import pandas as pd
import streamlit as st

DISPLAY_COLUMNS = {
    "ticker": "コード",
    "company_name": "銘柄名",
    "current_yield": "現在利回り",
    "avg_yield_5y": "5年平均利回り",
    "yield_gap_ratio": "乖離率",
    "market_cap": "時価総額",
    "equity_ratio": "自己資本比率(%)",
    "consecutive_no_cut_years": "連続非減配年数",
    "per": "PER",
    "pbr": "PBR",
    "buy_signal": "買いサイン",
}


def render_result_table(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("条件に合致する銘柄がありません。フィルタを緩めてください。")
        return

    sorted_df = df.sort_values("yield_gap_ratio", ascending=False).copy()

    display_df = sorted_df[[c for c in DISPLAY_COLUMNS if c in sorted_df.columns]].rename(
        columns=DISPLAY_COLUMNS
    )

    # 表示用にパーセント・億円換算
    if "現在利回り" in display_df.columns:
        display_df["現在利回り"] = (display_df["現在利回り"] * 100).round(2).astype(str) + "%"
    if "5年平均利回り" in display_df.columns:
        display_df["5年平均利回り"] = (display_df["5年平均利回り"] * 100).round(2).astype(str) + "%"
    if "乖離率" in display_df.columns:
        display_df["乖離率"] = (display_df["乖離率"] * 100).round(1).astype(str) + "%"
    if "時価総額" in display_df.columns:
        display_df["時価総額"] = (display_df["時価総額"] / 1e8).round(0).astype("Int64").astype(str) + "億円"
    if "買いサイン" in display_df.columns:
        display_df["買いサイン"] = display_df["買いサイン"].map({True: "🟢 買い", False: ""})

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    buy_count = int(sorted_df["buy_signal"].sum()) if "buy_signal" in sorted_df.columns else 0
    st.caption(f"表示件数: {len(sorted_df)}件（うち買いサイン: {buy_count}件）")
