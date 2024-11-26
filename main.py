import streamlit as st
from database import Database
from ai_advisor import AIAdvisor
from visualization import create_radar_chart, create_trend_chart, create_growth_chart
from components import display_manager_list, display_score_details
from utils import calculate_company_average, format_scores_for_ai

st.set_page_config(
    page_title="マネージャー評価・育成支援ダッシュボード",
    layout="wide"
)

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'dashboard'
if 'selected_manager' not in st.session_state:
    st.session_state.selected_manager = None

# Initialize database
try:
    db = Database()
except Exception as e:
    st.error(f"データベース接続エラー: {str(e)}")
    st.stop()

# Initialize AI advisor
try:
    ai_advisor = AIAdvisor()
except Exception as e:
    st.warning("AI機能は現在利用できません。基本機能のみ使用可能です。")
    ai_advisor = None

# Main navigation
st.sidebar.title("ナビゲーション")
page = st.sidebar.radio(
    "ページ選択",
    ["ダッシュボード", "マネージャー詳細", "評価指標設定"],
    key="navigation"
)

if page == "ダッシュボード":
    st.title("企業全体のマネージャー評価ダッシュボード")

    # Get all managers data
    managers_df = db.get_all_managers()
    
    # Calculate and display company average
    company_avg = calculate_company_average(managers_df)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Display radar chart
        radar_fig = create_radar_chart(
            list(company_avg.values()),
            "企業全体の平均スコア"
        )
        st.plotly_chart(radar_fig, use_container_width=True)
        
    with col2:
        st.subheader("企業全体の評価サマリー")
        for metric, score in company_avg.items():
            st.metric(label=metric.title(), value=f"{score:.1f}/5.0")
    
    # AI Suggestions
    if ai_advisor:
        st.subheader("AI改善提案")
        try:
            ai_suggestions = ai_advisor.generate_improvement_suggestions(company_avg)
            st.write(ai_suggestions)
        except Exception as e:
            st.warning("AI提案の生成中にエラーが発生しました")
    
    # Manager List
    st.markdown("---")
    display_manager_list(managers_df)

elif page == "マネージャー詳細":
    st.title("マネージャー詳細評価")
    
    if st.session_state.selected_manager:
        manager_data = db.get_manager_details(st.session_state.selected_manager)
        latest_scores = manager_data.iloc[0]
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Individual radar chart
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
        
        # Trend Analysis
        st.subheader("評価推移")
        trend_fig = create_trend_chart(manager_data)
        st.plotly_chart(trend_fig, use_container_width=True)
        
        # Growth Analysis
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
        
        # AI Suggestions
        if ai_advisor:
            st.subheader("個別AI改善提案")
            try:
                individual_scores = format_scores_for_ai(latest_scores)
                ai_suggestions = ai_advisor.generate_improvement_suggestions(individual_scores)
                st.write(ai_suggestions)
            except Exception as e:
                st.warning("AI提案の生成中にエラーが発生しました")
        
    else:
        st.info("マネージャーを選択してください")
elif page == "評価指標設定":
    st.title("評価指標設定")
    
    # 現在の評価指標を表示
    metrics_df = db.get_evaluation_metrics()
    
    st.subheader("現在の評価指標")
    for _, metric in metrics_df.iterrows():
        with st.expander(f"{metric['name']} ({metric['category']})"):
            st.write(f"説明: {metric['description']}")
            st.write(f"重み付け: {metric['weight']}")
    
    # 新しい評価指標の追加
    st.markdown("---")
    st.subheader("新しい評価指標の追加")
    
    with st.form("new_metric_form"):
        metric_name = st.text_input("指標名")
        metric_desc = st.text_area("説明")
        metric_category = st.selectbox("カテゴリー", ["core", "custom"])
        metric_weight = st.slider("重み付け", 0.1, 2.0, 1.0, 0.1)
        
        submit_button = st.form_submit_button("追加")
        
        if submit_button and metric_name and metric_desc:
            try:
                db.add_evaluation_metric(metric_name, metric_desc, metric_category, metric_weight)
                st.success("新しい評価指標が追加されました")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"評価指標の追加中にエラーが発生しました: {str(e)}")

