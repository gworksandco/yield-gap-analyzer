"""
優良株配当利回り乖離スクリーナー

data/results.csv（GitHub Actionsの夜間バッチが書き出す）を読むだけで、
計算処理は一切行わない構成（ネットキャッシュ版と同じ設計）。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.components.affiliate import render_affiliate  # noqa: E402
from app.components.disclaimer import render_disclaimer  # noqa: E402
from app.components.filters import apply_filters, render_filters  # noqa: E402
from app.components.result_table import render_result_table  # noqa: E402

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "results.csv"

st.set_page_config(page_title="優良株配当利回り乖離スクリーナー", layout="wide")


@st.cache_data(ttl=3600)
def load_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(DATA_PATH)


def render_logic_popover() -> None:
    with st.popover("📖 計算ロジックについて"):
        st.markdown(
            """
**利回り乖離率**
```
乖離率 = (現在の利回り ÷ 過去5年平均利回り) － 1
```
- 利回りはいずれも「実績配当 ÷ その期の株価」で統一計算（予想利回りは使用しません）
- 配当が無い年・データ欠損年は利回り0として過去5年平均に含めます
- 過去5年平均利回りが0の銘柄は乖離率を計算できないため0として扱います

**買いサイン**

サイドバーの「利回り乖離率の下限」以上の銘柄に🟢が表示されます。
現在の利回りが過去5年平均よりどれだけ上振れしているかの目安です。

**優良株フィルタ**

時価総額・自己資本比率・連続非減配年数・PER・PBRで絞り込めます。
データが取得できていない項目（空欄）は、その条件では除外されません。

**連続非減配年数について（データ上限にご注意ください）**

配当データは**最大10年分**しか保持していないため、連続非減配年数は
最大9年までしか判定できません。実際には10年を超えて増配・非減配を
継続している銘柄でも、本アプリ上は「9」が上限として表示されます。
            """
        )


def main() -> None:
    st.title("優良株配当利回り乖離スクリーナー")
    render_logic_popover()

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
    render_affiliate()
    render_disclaimer()


if __name__ == "__main__":
    main()
