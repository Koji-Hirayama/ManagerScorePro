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
        
        # AI提案と履歴
        if st.session_state.ai_advisor:
            st.subheader("🤖 AI改善提案・履歴管理")
            
            try:
                # AI提案の生成と表示
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown("### 🤖 AI改善提案")
                    if st.button("✨ 新しい提案を生成", type="primary"):
                        with st.spinner("AI提案を生成中..."):
                            ai_suggestions = st.session_state.ai_advisor.generate_improvement_suggestions(company_avg)
                            if ai_suggestions:
                                st.markdown("### 最新の提案")
                                st.write(ai_suggestions)
                                # 提案を保存
                                try:
                                    st.session_state.ai_advisor.save_suggestion(
                                        manager_id=None,  # 企業全体の提案
                                        suggestion_text=ai_suggestions
                                    )
                                    st.success("新しい提案が生成され、履歴に保存されました")
                                except Exception as e:
                                    st.error(f"提案の保存中にエラーが発生しました: {str(e)}")
                
                with col2:
                    # AI提案の実装状況の統計
                    try:
                        stats_query = """
                            SELECT 
                                COUNT(*) as total_suggestions,
                                SUM(CASE WHEN is_implemented THEN 1 ELSE 0 END) as implemented_count,
                                ROUND(AVG(CASE WHEN effectiveness_rating IS NOT NULL 
                                    THEN effectiveness_rating ELSE NULL END), 1) as avg_effectiveness
                            FROM ai_suggestion_history
                            WHERE manager_id IS NULL;
                        """
                        suggestion_stats = db.execute_query(stats_query)
                        if suggestion_stats and len(suggestion_stats) > 0:
                            stats = suggestion_stats[0]
                            st.metric("総提案数", stats['total_suggestions'])
                            if stats['total_suggestions'] > 0:
                                implemented_rate = (stats['implemented_count'] / stats['total_suggestions'] * 100)
                                st.metric("実装率", f"{implemented_rate:.1f}%")
                            if stats['avg_effectiveness']:
                                st.metric("平均効果", f"{stats['avg_effectiveness']}/5.0")
                    except Exception as e:
                        st.warning("統計情報の取得中にエラーが発生しました")
                
                # AI提案履歴の表示
                try:
                    st.markdown("### 📋 最近の提案履歴")
                    recent_suggestions = db.execute_query("""
                        SELECT 
                            sh.id,
                            COALESCE(m.name, '企業全体') as manager_name,
                            COALESCE(m.department, '-') as department,
                            sh.suggestion_text,
                            sh.created_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Tokyo' as created_at,
                            sh.is_implemented,
                            sh.effectiveness_rating
                        FROM ai_suggestion_history sh
                        LEFT JOIN managers m ON sh.manager_id = m.id
                        ORDER BY sh.created_at DESC
                        LIMIT 5;
                    """)
                    
                    if recent_suggestions:
                        for suggestion in recent_suggestions:
                            with st.expander(f"提案 ({suggestion['created_at'].strftime('%Y/%m/%d %H:%M')}) - {suggestion['manager_name']} ({suggestion['department']})"):
                                st.write(suggestion['suggestion_text'])
                                status = "✅ 実装済み" if suggestion['is_implemented'] else "⏳ 未実装"
                                effectiveness = f"効果: {'⭐' * suggestion['effectiveness_rating'] if suggestion['effectiveness_rating'] else '未評価'}"
                                st.caption(f"{status} | {effectiveness}")
                    else:
                        st.info("まだAI提案の履歴がありません")
                        
                except Exception as e:
                    st.error(f"AI提案履歴の表示中にエラーが発生しました: {str(e)}")

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
