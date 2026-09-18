"""アフィリエイト広告表示（A8.net）。"""

from __future__ import annotations

import streamlit as st

_AD_HTML = """
<div style="text-align: center; margin: 1.5rem 0;">
  <a href="https://px.a8.net/svt/ejp?a8mat=4BCE3O+D15LGY+2U8+100AO1" rel="nofollow">
    <img border="0" width="300" height="250" alt=""
         src="https://www25.a8.net/svt/bgt?aid=260918628788&wid=001&eno=01&mid=s00000000368006048000&mc=1">
  </a>
  <img border="0" width="1" height="1"
       src="https://www13.a8.net/0.gif?a8mat=4BCE3O+D15LGY+2U8+100AO1" alt="">
</div>
"""


def render_affiliate() -> None:
    st.markdown(
        """
##### 代わり映えない日常に、変化を。
配当を眺めるだけでなく、たまには自分へのご褒美も。
週末は、こだわりのお取り寄せグルメで少し贅沢な時間を過ごしてみませんか。

<span style="font-size: 0.75rem; color: #888;">[PR]</span>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(_AD_HTML, unsafe_allow_html=True)
