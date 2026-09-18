"""
Yield-Gap Analyzer（高配当優良株の過去平均利回り乖離スクリーナー）

data/results.csv（GitHub Actionsの夜間バッチが書き出す）を読むだけで、
計算処理は一切行わない構成（ネットキャッシュ版と同じ設計）。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.components.disclaimer import render_disclaimer  # noqa: E402
from app.components.filters import apply_filters, render_filters  # noqa: E402
from app.components.result_table import render_result_table  # noqa: E402

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "results.csv"

st.set_page_config(page_title="Yield-Gap Analyzer", layout="wide")


@st.cache_data(ttl=3600)
def load_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(DATA_PATH)


def main() -> None:
    st.title("Yield-Gap Analyzer")
    st.caption("高配当優良株の過去平均利回り乖離スクリーナー")

    df = load_data()

    if df.empty:
        st.warning(
            "スキャン結果データがまだありません。GitHub Actionsのバッチ実行完了後に表示されます。"
        )
        render_disclaimer()
        return

    last_updated = df["last_updated"].iloc[0] if "last_updated" in df.columns else "不明"
    st.caption(f"最終更新: {last_updated}（対象銘柄数: {len(df)}）")

    filters = render_filters()
    filtered_df = apply_filters(df, filters)

    render_result_table(filtered_df)
    render_disclaimer()


if __name__ == "__main__":
    main()
