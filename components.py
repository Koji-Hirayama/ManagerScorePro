import streamlit as st

def display_manager_list(managers_df):
    if managers_df.empty:
        st.warning("マネージャーデータが見つかりません")
        return

    # ヘッダー部分の表示
    with st.container():
        cols = st.columns([2, 4, 1])
        headers = ["マネージャー情報", "評価スコア", "アクション"]
        for col, header in zip(cols, headers):
            with col:
                st.markdown(f"**{header}**")
        st.markdown("---")

    # マネージャーリストの表示
    for _, manager in managers_df.iterrows():
        with st.container():
            col1, col2, col3 = st.columns([2, 4, 1])
            
            # マネージャー基本情報
            with col1:
                st.markdown(f"### {manager['name']}")
                st.caption(f"📊 部門: {manager['department']}")
            
            # スコア情報
            with col2:
                col_a, col_b = st.columns(2)
                scores = {
                    "🗣️ コミュニケーション": manager['avg_communication'],
                    "🤝 サポート": manager['avg_support'],
                    "🎯 目標管理": manager['avg_goal'],
                    "👥 リーダーシップ": manager['avg_leadership'],
                    "💡 問題解決力": manager['avg_problem'],
                    "📈 戦略": manager['avg_strategy']
                }
                
                # スコアを2列に分けて表示
                for i, (metric, score) in enumerate(scores.items()):
                    with col_a if i < 3 else col_b:
                        st.metric(
                            label=metric,
                            value=f"{score:.1f}",
                            delta=f"{score:.1f}/5.0"
                        )
            
            # アクションボタン
            with col3:
                st.write("")  # スペース調整
                st.write("")  # スペース調整
                if st.button("👉 詳細を見る", key=f"btn_manager_{manager['id']}"):
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