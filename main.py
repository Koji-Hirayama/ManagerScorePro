import streamlit as st
from database import Database
from ai_advisor import AIAdvisor
from visualization import create_radar_chart, create_trend_chart
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

# Initialize classes
db = Database()
ai_advisor = AIAdvisor()

# Main navigation
st.sidebar.title("ナビゲーション")
page = st.sidebar.radio(
    "ページ選択",
    ["ダッシュボード", "マネージャー詳細"],
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
    st.subheader("AI改善提案")
    ai_suggestions = ai_advisor.generate_improvement_suggestions(company_avg)
    st.write(ai_suggestions)
    
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
        
        # AI Suggestions
        st.subheader("個別AI改善提案")
        individual_scores = format_scores_for_ai(latest_scores)
        ai_suggestions = ai_advisor.generate_improvement_suggestions(individual_scores)
        st.write(ai_suggestions)
        
    else:
        st.info("マネージャーを選択してください")
