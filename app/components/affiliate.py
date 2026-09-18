"""アフィリエイト広告表示（A8.net）。"""

from __future__ import annotations

import streamlit as st

_GOURMET_AD_HTML = """
<a href="https://px.a8.net/svt/ejp?a8mat=4BCE3O+D15LGY+2U8+100AO1" rel="nofollow">
  <img border="0" width="300" height="250" alt=""
       src="https://www25.a8.net/svt/bgt?aid=260918628788&wid=001&eno=01&mid=s00000000368006048000&mc=1">
</a>
<img border="0" width="1" height="1"
     src="https://www13.a8.net/0.gif?a8mat=4BCE3O+D15LGY+2U8+100AO1" alt="">
"""

_SAKE_AD_HTML = """
<a href="https://px.a8.net/svt/ejp?a8mat=4BC6B5+G3ASDU+5V1I+HVNAP" rel="nofollow">
  <img border="0" width="300" height="250" alt=""
       src="https://www20.a8.net/svt/bgt?aid=260908529973&wid=001&eno=01&mid=s00000027351003003000&mc=1">
</a>
<img border="0" width="1" height="1"
     src="https://www15.a8.net/0.gif?a8mat=4BC6B5+G3ASDU+5V1I+HVNAP" alt="">
"""

# コピーの行数が広告ごとに違っても画像の位置が揃うよう、テキスト部分の高さを固定する
_COPY_BOX_HEIGHT_PX = 110

_PR_LABEL = '<span style="font-size: 0.75rem; color: #888;">[PR]</span>'


def _render_ad_block(heading: str, body: str, ad_html: str) -> str:
    return f"""
<div style="text-align: center;">
  <div style="min-height: {_COPY_BOX_HEIGHT_PX}px;">
    <p style="font-weight: 600; font-size: 1rem; margin-bottom: 0.3rem;">{heading}</p>
    <p style="font-size: 0.9rem; color: inherit; margin-bottom: 0.3rem;">{body}</p>
    {_PR_LABEL}
  </div>
  <div style="margin-top: 0.5rem;">
    {ad_html}
  </div>
</div>
"""


def render_affiliate() -> None:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            _render_ad_block(
                "代わり映えない日常に、変化を。",
                "配当を眺めるだけでなく、たまには自分へのご褒美も。"
                "週末は、こだわりのお取り寄せグルメで少し贅沢な時間を過ごしてみませんか。",
                _GOURMET_AD_HTML,
            ),
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            _render_ad_block(
                "特別な一本で、乾杯を。",
                "頑張った自分へ、大切な人へ。"
                "なかなか出会えない希少なお酒で、特別なひとときを。",
                _SAKE_AD_HTML,
            ),
            unsafe_allow_html=True,
        )
