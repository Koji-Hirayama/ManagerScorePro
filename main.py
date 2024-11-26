from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
from database import DatabaseManager
from visualization import create_radar_chart, create_department_comparison_chart
from components import display_manager_list
from ai_advisor import AIAdvisor
from utils import calculate_company_average

# Page configuration
st.set_page_config(
    page_title="マネージャー評価・育成支援ダッシュボード",
    layout="wide",
    page_icon="📊"
)

# Load custom CSS
with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Initialize session state
if 'selected_manager' not in st.session_state:
    st.session_state.selected_manager = None

# Initialize database
try:
    db = DatabaseManager()
except Exception as e:
    st.error(f"データベース接続エラー: {str(e)}")
    st.stop()

# Initialize AI advisor
try:
    st.session_state.ai_advisor = AIAdvisor()
except Exception as e:
    st.warning("AI機能は現在利用できません。基本機能のみ使用可能です。")
    st.session_state.ai_advisor = None

# Main content
st.title("企業全体のマネージャー評価ダッシュボード")

# 日付フィルター
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("開始日", value=datetime.now() - timedelta(days=180))
with col2:
    end_date = st.date_input("終了日", value=datetime.now())

try:
    # データの取得
    managers_df = db.get_all_managers(start_date=start_date, end_date=end_date)
    
    if managers_df.empty:
        st.warning("選択された期間のデータが見つかりません")
    else:
        # 全体平均の表示
        company_avg = calculate_company_average(managers_df)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # レーダーチャートの表示
            radar_fig = create_radar_chart(
                list(company_avg.values()),
                "企業全体の平均スコア"
            )
            st.plotly_chart(radar_fig, use_container_width=True)
        
        with col2:
            st.subheader("企業全体の評価サマリー")
            for metric, score in company_avg.items():
                st.metric(label=metric.title(), value=f"{score:.1f}/5.0")
        
        # 部門別分析
        st.subheader("部門別分析")
        dept_data = db.get_department_statistics()
        if not dept_data.empty:
            dept_fig = create_department_comparison_chart(dept_data)
            st.plotly_chart(dept_fig, use_container_width=True)
        
        # AI提案
        if st.session_state.ai_advisor:
            st.subheader("AI改善提案")
            try:
                ai_suggestions = st.session_state.ai_advisor.generate_improvement_suggestions(company_avg)
                st.write(ai_suggestions)
            except Exception as e:
                st.warning("AI提案の生成中にエラーが発生しました")
        
        # マネージャー一覧
        st.markdown("---")
        display_manager_list(managers_df)

except Exception as e:
    st.error(f"データの表示中にエラーが発生しました: {str(e)}")

# ナビゲーション情報
st.sidebar.markdown("### ナビゲーション")
st.sidebar.info("""
- 📊 ダッシュボード
- 📋 評価指標設定
- 👥 マネージャー一覧
- 📈 マネージャー詳細
""")

# System information
st.sidebar.markdown("### システム情報")
st.sidebar.info(f"最終更新: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}")