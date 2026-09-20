"""関連サイトへの相互リンク表示。"""
from __future__ import annotations

import streamlit as st


def render_related_sites() -> None:
    st.markdown("---")
    st.markdown("##### 🔗 関連サイト")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            "**清原銘柄ネットキャッシュ比率スクリーナー**\n\n"
            "財務の安全性で選ぶ、割安放置株スクリーニング\n\n"
            "[サイトを開く →](https://netcash-screener-6buc7hzelcykapkfdstyu7.streamlit.app/)"
        )
    with col2:
        st.markdown(
            "**米国株 利回り乖離スクリーナー**\n\n"
            "S&P500の高配当優良株を同じ基準で判定\n\n"
            "[サイトを開く →](https://yield-gap-analyzer-us-bfrwcen6dvkvdrmy7z8wkb.streamlit.app/)"
        )
