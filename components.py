import streamlit as st

def display_manager_list(managers_df):
    """マネージャー一覧を構造化されたリストで表示"""
    if managers_df.empty:
        st.warning("マネージャーデータが見つかりません")
        return

    # カスタムCSS
    st.markdown("""
    <style>
    .manager-header {
        background-color: #f0f2f6;
        padding: 0.5rem;
        border-radius: 0.5rem;
        margin-bottom: 0.3rem;
        display: flex;
        align-items: center;
    }
    .manager-row {
        padding: 0.5rem 0;
        border-bottom: 1px solid #e6e6e6;
        margin-bottom: 0.3rem;
    }
    .metric-container {
        background-color: white;
        padding: 0.3rem;
        border-radius: 0.3rem;
        border: 1px solid #e6e6e6;
        margin: 0;
    }
    .metric-value {
        font-size: 0.9rem;
        font-weight: bold;
        margin: 0;
        padding: 0;
    }
    .metric-label {
        font-size: 0.8rem;
        margin: 0;
        padding: 0;
    }
    .manager-name {
        font-size: 1.1rem;
        font-weight: bold;
        margin: 0 0 0.2rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

    # ヘッダーセクション
    cols = st.columns([2, 6, 1])
    with cols[0]:
        st.markdown("### 👤 基本情報")
    with cols[1]:
        st.markdown("### 📊 評価スコア")
    with cols[2]:
        st.markdown("### ⚡ アクション")
    st.markdown("<hr style='margin: 0.5rem 0'>", unsafe_allow_html=True)

    # マネージャーリストの表示
    for _, manager in managers_df.iterrows():
        with st.container():
            st.markdown('<div class="manager-row">', unsafe_allow_html=True)
            cols = st.columns([2, 6, 1])
            
            # 基本情報
            with cols[0]:
                st.markdown(f'<div class="manager-name">{manager["name"]}</div>', unsafe_allow_html=True)
                st.markdown(f"**部門**: {manager['department']}")
            
            # スコア情報
            with cols[1]:
                metric_cols = st.columns(6)
                metrics = {
                    "🗣️ コミュニケーション": manager['avg_communication'],
                    "🤝 サポート": manager['avg_support'],
                    "🎯 目標管理": manager['avg_goal'],
                    "👥 リーダーシップ": manager['avg_leadership'],
                    "💡 問題解決力": manager['avg_problem'],
                    "📈 戦略": manager['avg_strategy']
                }
                
                for (label, score), col in zip(metrics.items(), metric_cols):
                    with col:
                        st.markdown(
                            f'''
                            <div class="metric-container">
                                <div class="metric-label">{label}</div>
                                <div class="metric-value">{score:.1f}/5.0</div>
                            </div>
                            ''',
                            unsafe_allow_html=True
                        )
            
            # アクションボタン
            with cols[2]:
                if st.button("👉 詳細", key=f"btn_manager_{manager['id']}", use_container_width=True):
                    st.session_state.selected_manager = manager['id']
                    st.switch_page("pages/_manager_detail.py")
            
            st.markdown('</div>', unsafe_allow_html=True)

def display_score_details(scores):
    """スコアの詳細表示"""
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
