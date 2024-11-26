import os
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
if 'ai_advisor' not in st.session_state:
    try:
        st.session_state.ai_advisor = AIAdvisor()
    except Exception as e:
        st.warning(f"AI機能の初期化中にエラーが発生しました: {str(e)}")
        st.session_state.ai_advisor = None

# Ensure OpenAI API key is available
if not os.getenv('OPENAI_API_KEY'):
    st.error("OpenAI APIキーが設定されていません。AI機能は利用できません。")
    st.session_state.ai_advisor = None

# Main content
st.title("マネージャー評価ダッシュボード")

try:
    # データの取得
    managers_df = db.get_all_managers()
    
    if managers_df.empty:
        st.warning("マネージャーデータが見つかりません")
    else:
        # 全体平均の表示
        st.subheader("📊 企業全体の評価サマリー")
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
            for metric, score in company_avg.items():
                st.metric(label=metric.title(), value=f"{score:.1f}/5.0")
        
        # AI提案
        if st.session_state.ai_advisor:
            st.subheader("🤖 AI改善提案")
            try:
                ai_suggestions = st.session_state.ai_advisor.generate_improvement_suggestions(company_avg)
                st.write(ai_suggestions)
            except Exception as e:
                st.warning("AI提案の生成中にエラーが発生しました")

        st.markdown("---")
        
        # 部門別分析
        st.subheader("📈 部門別分析")
        dept_data = db.get_department_statistics()
        if not dept_data.empty:
            dept_fig = create_department_comparison_chart(dept_data)
            st.plotly_chart(dept_fig, use_container_width=True)

        st.markdown("---")
        
        # マネージャー一覧の表示
        st.subheader("👥 マネージャー一覧")
        display_manager_list(managers_df)

except Exception as e:
    st.error(f"データの表示中にエラーが発生しました: {str(e)}")
