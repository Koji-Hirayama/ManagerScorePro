import streamlit as st
from database import DatabaseManager
from datetime import datetime
from ai_advisor import AIAdvisor
from visualization import create_radar_chart, create_trend_chart, create_growth_chart
from components import display_score_details
from utils import format_scores_for_ai

st.title("マネージャー詳細評価")

if not st.session_state.get('selected_manager'):
    st.info("ダッシュボードからマネージャーを選択してください")
    st.stop()

try:
    db = DatabaseManager()
    manager_data = db.get_manager_details(st.session_state.selected_manager)
    
    if manager_data.empty:
        st.warning("マネージャーデータが見つかりません")
        st.stop()
        
    latest_scores = manager_data.iloc[0]
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        radar_fig = create_radar_chart(
            [
                latest_scores.communication_score,
                latest_scores.support_score,
                latest_scores.goal_management_score,
                latest_scores.leadership_score,
                latest_scores.problem_solving_score,
                latest_scores.strategy_score
            ],
            "個人評価スコア"
        )
        st.plotly_chart(radar_fig, use_container_width=True)
        
    with col2:
        display_score_details(latest_scores)
    
    # トレンド分析
    st.subheader("評価推移")
    trend_fig = create_trend_chart(manager_data)
    st.plotly_chart(trend_fig, use_container_width=True)
    
    # 成長分析
    st.subheader("成長分析")
    growth_data = db.analyze_growth(st.session_state.selected_manager)
    if not growth_data.empty:
        growth_fig = create_growth_chart(growth_data)
        st.plotly_chart(growth_fig, use_container_width=True)
        
        # 最新の成長率を表示
        latest_growth = growth_data.iloc[0]['growth_rate']
        st.metric(
            label="直近の成長率",
            value=f"{latest_growth:.1f}%",
            delta=f"{latest_growth:.1f}%" if latest_growth > 0 else f"{latest_growth:.1f}%"
        )
    
    # AI提案
    if hasattr(st, 'ai_advisor'):
        st.subheader("個別AI改善提案")
        try:
            individual_scores = format_scores_for_ai(latest_scores)
            ai_suggestions = st.ai_advisor.generate_improvement_suggestions(individual_scores)
            st.write(ai_suggestions)
        except Exception as e:
            st.warning("AI提案の生成中にエラーが発生しました")
            
# レポート生成セクション
    st.markdown("---")
    st.subheader("評価レポート")
    
    if st.button("レポートを生成"):
        with st.spinner("レポートを生成中..."):
            from report_generator import generate_manager_report, export_report_to_markdown
            
            report_content = generate_manager_report(
                manager_data,
                growth_data,
                st.session_state.get('ai_advisor')
            )
            
            if report_content:
                st.markdown(report_content)
                
                # レポートのダウンロード機能
                filename = f"manager_report_{latest_scores['name']}_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
                if export_report_to_markdown(report_content, filename):
                    with open(filename, 'r', encoding='utf-8') as f:
                        st.download_button(
                            label="レポートをダウンロード",
                            data=f.read(),
                            file_name=filename,
                            mime="text/markdown"
                        )
            else:
                st.error("レポートの生成中にエラーが発生しました")

except Exception as e:
    st.error(f"マネージャー詳細の表示中にエラーが発生しました: {str(e)}")
