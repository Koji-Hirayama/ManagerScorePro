import os
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
from database import DatabaseManager
from visualization import create_radar_chart, create_trend_chart, create_growth_chart
from components import display_score_details
from utils import format_scores_for_ai
from report_generator import generate_manager_report, export_report_to_markdown
from ai_advisor import AIAdvisor

st.title("マネージャー詳細評価")

# サイドバーにAI設定を追加
with st.sidebar:
    st.subheader("AI設定")
    
    # AIモデルの選択（デフォルトはgpt-3.5-turbo）
    if 'ai_model' not in st.session_state:
        st.session_state.ai_model = 'gpt-3.5-turbo'

    # サイドバーにAIモデル選択を追加
    st.session_state.ai_model = st.sidebar.selectbox(
        "AIモデルの選択",
        options=['gpt-3.5-turbo', 'gpt-4'],
        help="より高度な提案にはGPT-4を、より速い応答にはGPT-3.5を選択してください。"
    )
    
    cache_hours = st.slider(
        "キャッシュ有効期限（時間）",
        min_value=1,
        max_value=72,
        value=24,
        help="AI提案のキャッシュを保持する時間を設定します"
    )
    if 'ai_advisor' in st.session_state:
        st.session_state.ai_advisor.cache_expiry = timedelta(hours=cache_hours)
        
        # キャッシュ状態の表示
        stats = st.session_state.ai_advisor.cache_stats
        st.markdown("### キャッシュ状態")
        st.write(f"総エントリー数: {stats['total_entries']}")
        st.write(f"有効: {stats['valid_entries']}")
        st.write(f"期限切れ: {stats['expired_entries']}")
        
        if st.button("キャッシュをクリア"):
            st.session_state.ai_advisor.clear_cache()
            st.success("キャッシュをクリアしました")

if not st.session_state.get('selected_manager'):
    st.info("ダッシュボードからマネージャーを選択してください")
    st.stop()

try:
    # データベース初期化
    db = DatabaseManager()
    manager_data = db.get_manager_details(st.session_state.selected_manager)
    
    if manager_data.empty:
        st.warning("マネージャーデータが見つかりません")
        st.stop()
        
    latest_scores = manager_data.iloc[0]
    
    # マネージャー情報を表示
    st.header(f"👤 {latest_scores['name']}")
    st.subheader(f"📋 部門: {latest_scores['department']}")
    st.markdown("---")
    
    # 評価スコアと可視化のタブ
    tab1, tab2, tab3 = st.tabs(["📊 評価スコア", "📈 成長分析", "🤖 AI提案履歴"])
    
    with tab1:
        col1, col2 = st.columns([2, 1])
        with col1:
            # 個人のレーダーチャート
            radar_fig = create_radar_chart(
                [
                    latest_scores['communication_score'],
                    latest_scores['support_score'],
                    latest_scores['goal_management_score'],
                    latest_scores['leadership_score'],
                    latest_scores['problem_solving_score'],
                    latest_scores['strategy_score']
                ],
                "個人評価スコア"
            )
            st.plotly_chart(radar_fig, use_container_width=True)
        
        with col2:
            display_score_details(latest_scores)
    
    with tab2:
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
            
            latest_growth = growth_data.iloc[0]['growth_rate']
            st.metric(
                label="直近の成長率",
                value=f"{latest_growth:.1f}%",
                delta=f"{latest_growth:.1f}%" if latest_growth > 0 else f"{latest_growth:.1f}%"
            )
    
    with tab3:
        st.subheader("AI提案履歴")
        
        # OpenAI APIキーの存在確認
        if not os.getenv('OPENAI_API_KEY'):
            st.error("OpenAI APIキーが設定されていません。AI機能は利用できません。")
        elif not st.session_state.get('ai_advisor'):
            try:
                st.session_state.ai_advisor = AIAdvisor()
            except Exception as e:
                st.error(f"AI機能の初期化に失敗しました: {str(e)}")
        
        if st.session_state.get('ai_advisor'):
            try:
                # 新しい提案の生成
                with st.expander("✨ 新しい提案を生成", expanded=True):
                    # プロンプトテンプレートの管理
                    templates_df = st.session_state.ai_advisor.get_prompt_templates()
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        selected_template = st.selectbox(
                            "プロンプトテンプレートを選択",
                            options=[None] + templates_df['id'].tolist(),
                            format_func=lambda x: "デフォルト" if x is None else templates_df[templates_df['id'] == x]['name'].iloc[0],
                            help="使用するプロンプトテンプレートを選択してください"
                        )
                    
                    with col2:
                        if st.button("新規テンプレート", type="secondary"):
                            st.session_state.show_template_form = True
                    
                    # テンプレート情報の表示
                    if selected_template is not None:
                        template_info = templates_df[templates_df['id'] == selected_template].iloc[0]
                        with st.expander("テンプレート詳細", expanded=False):
                            st.markdown(f"**説明**: {template_info['description']}")
                            st.text_area("テンプレート内容", template_info['template_text'], disabled=True)
                    
                    # 新規テンプレートフォーム
                    if st.session_state.get('show_template_form', False):
                        st.markdown("### 新規テンプレートの作成")
                        with st.form("new_template_form"):
                            template_name = st.text_input(
                                "テンプレート名",
                                max_chars=100,
                                help="テンプレートの識別名を入力してください"
                            )
                            template_description = st.text_area(
                                "説明",
                                help="テンプレートの用途や特徴を説明してください"
                            )
                            template_text = st.text_area(
                                "テンプレート本文",
                                help="プロンプトのテンプレートを入力してください。{scores[項目名]}で評価スコアを参照できます"
                            )
                            
                            if st.form_submit_button("保存"):
                                try:
                                    st.session_state.ai_advisor.add_prompt_template(
                                        template_name,
                                        template_description,
                                        template_text
                                    )
                                    st.success("新しいテンプレートを保存しました")
                                    st.session_state.show_template_form = False
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"テンプレートの保存中にエラーが発生しました: {str(e)}")
                    
                    # 提案生成ボタン
                    if st.button("提案を生成", type="primary"):
                        with st.spinner("AI提案を生成中..."):
                            individual_scores = format_scores_for_ai(latest_scores)
                            ai_suggestions = st.session_state.ai_advisor.generate_improvement_suggestions(
                                individual_scores,
                                selected_template
                            )
                            if ai_suggestions and "エラー" not in ai_suggestions:
                                # 提案を保存
                                st.session_state.ai_advisor.save_suggestion(
                                    st.session_state.selected_manager,
                                    ai_suggestions
                                )
                                st.success("新しい提案が生成され、履歴に保存されました")
                            else:
                                st.error("AI提案の生成中にエラーが発生しました")
                
                # 提案履歴の表示
                suggestion_history = st.session_state.ai_advisor.get_suggestion_history(
                    st.session_state.selected_manager
                )
                
                if not suggestion_history.empty:
                    for _, suggestion in suggestion_history.iterrows():
                        with st.expander(
                            f"提案 ({suggestion['created_at'].strftime('%Y年%m月%d日 %H:%M')})",
                            expanded=False
                        ):
                            st.markdown("#### 提案内容")
                            st.write(suggestion['suggestion_text'])
                            
                            # NaN値のチェックを追加
                            if pd.notna(suggestion['feedback_text']):
                                st.markdown("#### フィードバック履歴")
                                st.info(suggestion['feedback_text'])
                            
                            # 実装状態の更新
                            col1, col2 = st.columns(2)
                            with col1:
                                is_implemented = st.checkbox(
                                    "実装済み",
                                    value=bool(suggestion['is_implemented']),  # bool型に変換
                                    key=f"impl_{suggestion['id']}"
                                )
                            
                            with col2:
                                effectiveness = st.select_slider(
                                    "効果評価",
                                    options=range(1, 6),
                                    value=int(suggestion['effectiveness_rating'] if pd.notna(suggestion['effectiveness_rating']) else 3),
                                    format_func=lambda x: ["非常に低い", "低い", "普通", "高い", "非常に高い"][x-1],
                                    key=f"effect_{suggestion['id']}"
                                )
                                
                                # フィードバックセクション
                                st.markdown("### フィードバック :red[*]")
                                feedback_text = st.text_area(
                                    "フィードバックコメント",
                                    key=f"feedback_{suggestion['id']}",
                                    placeholder="提案の効果や改善点について具体的に記入してください",
                                    help="提案の実装結果や効果、今後の改善点などを記録します（必須）",
                                    max_chars=500
                                )

                                # 文字数カウンター
                                if feedback_text:
                                    st.caption(f"文字数: {len(feedback_text)}/500")

                                # フィードバック履歴の表示
                                if pd.notna(suggestion['feedback_text']):
                                    st.markdown("#### 過去のフィードバック履歴")
                                    for i, feedback in enumerate(suggestion['feedback_text'].split('\n---\n'), 1):
                                        if feedback.strip():
                                            st.info(
                                                f"📝 フィードバック #{i}\n"
                                                f"{feedback.strip()}\n"
                                                f"🕒 {suggestion['created_at'].strftime('%Y年%m月%d日 %H:%M')}"
                                            )

                                # 実装状態と効果評価のバッジ表示
                                status_col1, status_col2 = st.columns(2)
                                with status_col1:
                                    st.markdown(
                                        f"実装状態: {'🟢 実装済み' if suggestion['is_implemented'] else '🔴 未実装'}"
                                    )
                                with status_col2:
                                    if pd.notna(suggestion['effectiveness_rating']):
                                        rating_emoji = ["⭐"] * int(suggestion['effectiveness_rating'])
                                        st.markdown(f"効果評価: {''.join(rating_emoji)}")
                            
                                # バリデーションと送信確認
                                if st.button("状態を更新", key=f"update_{suggestion['id']}", type="primary"):
                                    if not feedback_text.strip():
                                        st.error("フィードバックコメントは必須項目です")
                                    else:
                                        if st.button("更新を確定しますか？", key=f"confirm_{suggestion['id']}"):
                                            # 現在のフィードバックと過去のフィードバックを結合
                                            current_feedback = suggestion['feedback_text'] if pd.notna(suggestion['feedback_text']) else ""
                                            new_feedback = f"{feedback_text}\n---\n{current_feedback}" if current_feedback else feedback_text
                                            
                                            st.session_state.ai_advisor.update_suggestion_status(
                                                suggestion['id'],
                                                is_implemented=is_implemented,
                                                effectiveness_rating=effectiveness,
                                                feedback_text=new_feedback
                                            )
                                            st.success("提案の状態を更新しました")
                                            st.balloons()  # 視覚的なフィードバック
                else:
                    st.info("まだAI提案の履歴がありません")
                
            except Exception as e:
                st.error(f"AI提案履歴の表示中にエラーが発生しました: {str(e)}")
    
    # レポート生成セクション
    st.markdown("---")
    st.subheader("評価レポート")
    
    if st.button("レポートを生成"):
        with st.spinner("レポートを生成中..."):
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
