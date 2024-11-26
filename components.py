import streamlit as st

def display_manager_list(managers_df):
    st.subheader("マネージャー一覧")
    
    try:
        if managers_df.empty:
            st.warning("マネージャーデータが見つかりません")
            return
        
        # データテーブルとして表示
        display_df = managers_df[[
            'name', 'department',
            'avg_communication', 'avg_support', 'avg_goal',
            'avg_leadership', 'avg_problem', 'avg_strategy'
        ]].copy()
        
        # カラム名を日本語に変更
        display_df.columns = [
            '名前', '部門',
            'コミュニケーション', 'サポート', '目標管理',
            'リーダーシップ', '問題解決力', '戦略'
        ]
        
        # インタラクティブなデータテーブルを表示
        st.dataframe(
            display_df,
            column_config={
                '名前': st.column_config.Column(width=150),
                '部門': st.column_config.Column(width=100),
                'コミュニケーション': st.column_config.NumberColumn(format="%.1f", width=120),
                'サポート': st.column_config.NumberColumn(format="%.1f", width=120),
                '目標管理': st.column_config.NumberColumn(format="%.1f", width=120),
                'リーダーシップ': st.column_config.NumberColumn(format="%.1f", width=120),
                '問題解決力': st.column_config.NumberColumn(format="%.1f", width=120),
                '戦略': st.column_config.NumberColumn(format="%.1f", width=120)
            },
            hide_index=True
        )
        
        # 詳細ボタンを各行に追加
        for _, manager in managers_df.iterrows():
            if st.button(f"{manager['name']}の詳細を見る", key=f"btn_manager_{manager['id']}"):
                st.session_state.selected_manager = manager['id']
                st.switch_page("pages/manager_detail.py")
                
    except Exception as e:
        print(f"マネージャー一覧表示エラー: {str(e)}")
        st.error("マネージャー一覧の表示中にエラーが発生しました")

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
