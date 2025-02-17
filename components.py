import streamlit as st
from sqlalchemy import text

def get_score_color(score):
    """スコアに応じたカラーコードを返す"""
    if score >= 4.0:
        return "#28a745"  # 緑（優秀）
    elif score >= 3.0:
        return "#17a2b8"  # 青（良好）
    elif score >= 2.0:
        return "#ffc107"  # 黄（要改善）
    else:
        return "#dc3545"  # 赤（要注意）

def display_manager_list(managers_df):
    """マネージャー一覧を構造化されたリストで表示（フィルタリング機能付き）"""
    if managers_df.empty:
        st.warning("マネージャーデータが見つかりません")
        return

    # フィルターとソート設定
    st.subheader("🔍 フィルター & ソート設定")
    
    filter_col1, filter_col2, filter_col3 = st.columns([2, 2, 1])
    
    with filter_col1:
        name_filter = st.text_input(
            "🔍 名前で検索",
            key="name_filter",
            help="マネージャーの名前で部分一致検索（大文字小文字区別なし）"
        )
    
    with filter_col2:
        department_filter = st.selectbox(
            "🏢 部門でフィルター",
            options=["全て"] + sorted(managers_df["department"].unique().tolist()),
            key="department_filter",
            help="特定の部門のマネージャーのみを表示"
        )
    
    with filter_col3:
        if st.button("🔄 リセット", use_container_width=True):
            st.session_state.name_filter = ""
            st.session_state.department_filter = "全て"
            st.session_state.sort_column = 'name'
            st.session_state.sort_order = True
            st.rerun()

    # ソート設定
    sort_col1, sort_col2 = st.columns([3, 1])
    
    with sort_col1:
        sort_options = {
            'name': '👤 名前',
            'department': '🏢 部門',
            'avg_communication': '🗣️ コミュニケーション',
            'avg_support': '🤝 サポート',
            'avg_goal': '🎯 目標管理',
            'avg_leadership': '👥 リーダーシップ',
            'avg_problem': '💡 問題解決力',
            'avg_strategy': '📈 戦略'
        }
        
        sort_column = st.selectbox(
            "並び替え項目",
            options=list(sort_options.keys()),
            format_func=lambda x: sort_options[x],
            key="sort_column",
            help="一覧の並び替えに使用する項目を選択"
        )
    
    with sort_col2:
        sort_order = st.selectbox(
            "並び順",
            options=[True, False],
            format_func=lambda x: "⬆️ 昇順" if x else "⬇️ 降順",
            key="sort_order",
            help="昇順/降順を選択"
        )

    # フィルタリングとソートの適用
    filtered_df = managers_df.copy()

    # 名前フィルター
    if name_filter:
        filtered_df = filtered_df[filtered_df["name"].str.contains(name_filter, case=False, na=False)]

    # 部門フィルター
    if department_filter != "全て":
        filtered_df = filtered_df[filtered_df["department"] == department_filter]

    # ソート
    try:
        filtered_df = filtered_df.sort_values(by=sort_column, ascending=sort_order)
    except Exception as e:
        st.error(f"ソート処理中にエラーが発生しました: {str(e)}")
        filtered_df = filtered_df.sort_values(by='name', ascending=True)

    # フィルター後のデータ件数表示
    st.markdown(f"**表示件数**: {len(filtered_df)}件")
    
    if filtered_df.empty:
        st.info("条件に一致するマネージャーが見つかりません")
        return

    # 部門ごとにグループ化
    departments = sorted(filtered_df['department'].unique())
    department_groups = {dept: filtered_df[filtered_df['department'] == dept] for dept in departments}

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
        padding: 0.3rem;
        border-radius: 0.3rem;
        border: 1px solid #e6e6e6;
        margin: 0;
        transition: background-color 0.3s;
    }
    .metric-value {
        font-size: 0.9rem;
        font-weight: bold;
        margin: 0;
        padding: 0;
        color: white;
        text-shadow: 1px 1px 1px rgba(0,0,0,0.2);
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
    .department-header {
        background-color: #e1e4e8;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        font-weight: bold;
    }
    .department-stats {
        font-size: 0.9rem;
        color: #586069;
        margin-top: 0.5rem;
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

    # 部門ごとのマネージャーリスト表示
    for department in departments:
        dept_df = department_groups[department]
        
        # 部門ヘッダーと統計情報
        st.markdown(
            f"""
            <div class="department-header">
                🏢 {department}
                <div class="department-stats">
                    マネージャー数: {len(dept_df)}名 | 
                    平均評価: {dept_df[['avg_communication', 'avg_support', 'avg_goal', 
                                    'avg_leadership', 'avg_problem', 'avg_strategy']].mean().mean():.1f}/5.0
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # 部門ごとのマネージャー表示
        for _, manager in dept_df.iterrows():
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
                                <div class="metric-container" style="background-color: {get_score_color(score)}">
                                    <div class="metric-label" style="color: white">{label}</div>
                                    <div class="metric-value">{score:.1f}/5.0</div>
                                </div>
                                ''',
                                unsafe_allow_html=True
                            )
                
                # アクションボタン
                with cols[2]:
                    if st.button("👉 詳細", key=f"btn_manager_{manager['id']}", use_container_width=True):
                        st.session_state.selected_manager = manager['id']
                        st.switch_page("pages/3_Manager_Detail.py")
                
                st.markdown('</div>', unsafe_allow_html=True)

def display_score_details(scores):
    """スコアの詳細表示（カラーコード付き）"""
    metrics = {
        'コミュニケーション・フィードバック': scores['communication_score'],
        'サポート・エンパワーメント': scores['support_score'],
        '目標管理・成果達成': scores['goal_management_score'],
        'リーダーシップ・意思決定': scores['leadership_score'],
        '問題解決力': scores['problem_solving_score'],
        '戦略・成長支援': scores['strategy_score']
    }
    
    for metric, score in metrics.items():
        color = get_score_color(score)
        st.markdown(
            f"""
            <div style="
                background-color: {color};
                padding: 1rem;
                border-radius: 0.5rem;
                margin: 0.5rem 0;
                color: white;
                text-shadow: 1px 1px 1px rgba(0,0,0,0.2);
            ">
                <div style="font-size: 0.9rem;">{metric}</div>
                <div style="font-size: 1.2rem; font-weight: bold;">{score:.1f}/5.0</div>
            </div>
            """,
            unsafe_allow_html=True
        )
