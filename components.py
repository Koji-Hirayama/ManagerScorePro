import streamlit as st

def display_manager_list(managers_df):
    st.subheader("マネージャー一覧")
    
    try:
        if managers_df.empty:
            st.warning("マネージャーデータが見つかりません")
            return
            
        for _, manager in managers_df.iterrows():
            col1, col2 = st.columns([1, 4])
            
            with col1:
                st.write(f"{manager['name']} ({manager['department']})")
            
            with col2:
                try:
                    avg_score = (
                        float(manager['avg_communication']) +
                        float(manager['avg_support']) +
                        float(manager['avg_goal']) +
                        float(manager['avg_leadership']) +
                        float(manager['avg_problem']) +
                        float(manager['avg_strategy'])
                    ) / 6
                    
                    st.progress(min(avg_score / 5, 1.0))
                except (ValueError, TypeError) as e:
                    print(f"スコア計算エラー - マネージャー {manager['name']}: {str(e)}")
                    st.error("スコアの計算中にエラーが発生しました")
                
            # UUIDを使用してユニークなキーを生成
            unique_key = f"btn_manager_{manager['id']}_{manager['department']}"
            if st.button(f"{manager['name']}の詳細を見る", key=unique_key):
                st.session_state.selected_manager = manager['id']
                st.session_state.page = 'マネージャー詳細'
                st.experimental_rerun()
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
