"""スマホでの共有・ホーム画面追加を促すUIコンポーネント。

iOS Safariの「ホーム画面に追加」はOS標準の共有シートからユーザーが手動で
選ぶ操作のため、アプリ側のコードから直接開くことはできない。そのため
以下の2つを組み合わせて対応する:

1. Web Share API（navigator.share）を使った共有ボタンを設置する。
   iOS 16.4以降ではこの共有シートに「ホーム画面に追加」の選択肢も含まれるため、
   ボタンをタップするだけで共有・ホーム画面追加の両方に到達できる。
   Web Share API非対応環境（主にPCブラウザ）では、URLをクリップボードに
   コピーするフォールバックにする。
2. ホーム画面に追加した際のアイコン・タイトル表示を整えるため、
   apple-touch-icon等のメタタグをcomponents.htmlのiframe経由で
   親ドキュメント（実際のアプリ画面）のheadに注入する。
   クロスオリジン制限等で注入に失敗しても共有ボタン自体は動作する。
"""

from __future__ import annotations

import streamlit.components.v1 as components

APP_TITLE = "優良株配当利回り乖離スクリーナー"
APP_URL = "https://yield-gap-analyzer-nfqwcimerggfcozvrsbnga.streamlit.app/"
ICON_PATH = "/app/static/icon-180.png"  # .streamlit/config.toml の enableStaticServing 前提


def render_share_and_home_screen_hint() -> None:
    """タイトル上部に共有ボタンを表示し、ホーム画面アイコン用のメタタグを注入する。"""
    html = f"""
    <div style="display: flex; justify-content: flex-end; align-items: center; gap: 0.5rem; margin-bottom: 0.15rem;">
      <button id="share-btn" style="
        display: flex; align-items: center; gap: 0.3rem;
        background: transparent; border: 1px solid #888; border-radius: 999px;
        padding: 0.25rem 0.75rem; font-size: 0.8rem; cursor: pointer; color: #555;
      ">🔗 共有</button>
      <span id="share-msg" style="display:none; font-size: 0.72rem; color: #888;"></span>
    </div>
    <script>
      (function() {{
        try {{
          var parentDoc = window.parent.document;
          if (!parentDoc.querySelector('meta[name="apple-mobile-web-app-capable"]')) {{
            var m1 = parentDoc.createElement('meta');
            m1.name = 'apple-mobile-web-app-capable';
            m1.content = 'yes';
            parentDoc.head.appendChild(m1);

            var m2 = parentDoc.createElement('meta');
            m2.name = 'apple-mobile-web-app-title';
            m2.content = '{APP_TITLE}';
            parentDoc.head.appendChild(m2);

            var iconLink = parentDoc.createElement('link');
            iconLink.rel = 'apple-touch-icon';
            iconLink.href = window.parent.location.origin + '{ICON_PATH}';
            parentDoc.head.appendChild(iconLink);
          }}
        }} catch (e) {{
          // クロスオリジン制限等で失敗した場合はホーム画面アイコンの見た目向上のみ諦める
        }}

        var btn = document.getElementById('share-btn');
        var msg = document.getElementById('share-msg');

        btn.addEventListener('click', function() {{
          if (navigator.share) {{
            navigator.share({{ title: '{APP_TITLE}', url: '{APP_URL}' }}).catch(function() {{}});
          }} else if (navigator.clipboard) {{
            navigator.clipboard.writeText('{APP_URL}').then(function() {{
              msg.textContent = 'リンクをコピーしました';
              msg.style.display = 'inline';
              setTimeout(function() {{ msg.style.display = 'none'; }}, 2000);
            }});
          }} else {{
            msg.textContent = '{APP_URL}';
            msg.style.display = 'inline';
          }}
        }});
      }})();
    </script>
    """
    components.html(html, height=42)
