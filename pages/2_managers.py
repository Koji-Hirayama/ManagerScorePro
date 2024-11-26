import streamlit as st
from database import DatabaseManager
from components import display_manager_list

# ページ設定
st.set_page_config(
    page_title="マネージャー一覧 | スキル評価システム",
    page_icon="👥",
    layout="wide"
)

# タイトルセクション
st.markdown("# 👥 マネージャー一覧")
st.markdown("###  マネージャーのスキル評価と成長の追跡")

# 説明セクション
with st.container():
    st.markdown("""
    このページでは、各マネージャーの:
    - 📊 現在のスキル評価スコア
    - 🎯 主要な評価指標
    - 📈 成長の進捗
    を確認できます。詳細ボタンをクリックすると、より詳しい分析と提案を見ることができます。
    """)
    st.markdown("---")

try:
    # データベース初期化
    db = DatabaseManager()
    
    # マネージャーデータの取得
    managers_df = db.get_all_managers()
    
    # マネージャーリストの表示
    if managers_df.empty:
        st.warning("⚠️ マネージャーデータが見つかりません")
    else:
        display_manager_list(managers_df)
        
except Exception as e:
    st.error(f"❌ マネージャー一覧の表示中にエラーが発生しました: {str(e)}")
