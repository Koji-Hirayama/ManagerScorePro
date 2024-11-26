import streamlit as st

def display_manager_list(managers_df):
    st.subheader("マネージャー一覧")
    
    if managers_df.empty:
        st.warning("マネージャーデータが見つかりません")
        return
        
    for _, manager in managers_df.iterrows():
        with st.container():
            col1, col2, col3 = st.columns([2, 4, 1])
            
            with col1:
                st.write(f"**{manager['name']}**")
                st.caption(f"部門: {manager['department']}")
            
            with col2:
                scores = {
                    "コミュニケーション": manager['avg_communication'],
                    "サポート": manager['avg_support'],
                    "目標管理": manager['avg_goal'],
                    "リーダーシップ": manager['avg_leadership'],
                    "問題解決力": manager['avg_problem'],
                    "戦略": manager['avg_strategy']
                }
                
                for metric, score in scores.items():
                    st.write(f"{metric}: {score:.1f}")
            
            with col3:
                if st.button("詳細を見る", key=f"btn_manager_{manager['id']}"):
                    st.session_state.selected_manager = manager['id']
                    st.switch_page("pages/_manager_detail.py")
            
            st.markdown("---")

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