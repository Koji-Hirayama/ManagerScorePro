import streamlit as st

def display_manager_list(managers_df):
    st.subheader("マネージャー一覧")
    
    for _, manager in managers_df.iterrows():
        col1, col2 = st.columns([1, 4])
        
        with col1:
            st.write(manager['name'])
        
        with col2:
            avg_score = (
                manager['avg_communication'] +
                manager['avg_support'] +
                manager['avg_goal'] +
                manager['avg_leadership'] +
                manager['avg_problem'] +
                manager['avg_strategy']
            ) / 6
            
            st.progress(avg_score / 5)
            
        if st.button(f"{manager['name']}の詳細を見る", key=f"btn_{manager['id']}"):
            st.session_state.selected_manager = manager['id']
            st.session_state.page = 'detail'

def display_score_details(scores):
    metrics = {
        'コミュニケーション・フィードバック': scores['communication_score'],
        'サポート・エンパワーメント': scores['support_score'],
        '目標管理・成果達成': scores['goal_management_score'],
        'リーダーシップ・意思決定': scores['leadership_score'],
        '問題解決力': scores['problem_solving_score'],
        '戦略・成長支援': scores['strategy_score']
    }
    
    for metric, score in metrics.items():
        st.metric(label=metric, value=f"{score:.1f}/5.0")
