import components
import streamlit as st
from database import DatabaseManager
from ai_advisor import AIAdvisor
from visualization import (
    create_radar_chart, create_trend_chart, create_growth_chart,
    create_department_comparison_chart, create_department_metrics_chart
)
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
    db = DatabaseManager()
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
    ["ダッシュボード", "マネージャー詳細", "部門別分析", "評価指標設定"],
    key="navigation"
)

# ページ状態の更新を確実に行う
if page != st.session_state.page:
    st.session_state.page = page
    st.rerun()

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
    
    try:
        # 現在の評価指標を取得
        metrics_df = db.get_evaluation_metrics()
        
        # カテゴリー別に指標を整理
        st.subheader("現在の評価指標")
        categories = metrics_df['category'].unique()
        
        for category in categories:
            with st.expander(f"{category.upper()}カテゴリー", expanded=True):
                category_metrics = metrics_df[metrics_df['category'] == category]
                for _, metric in category_metrics.iterrows():
                    st.markdown(f"### {metric['name']}")
                    st.markdown(f"**説明**: {metric['description']}")
                    st.markdown(f"**重み付け**: {metric['weight']:.1f}")
                    st.markdown("---")
        
        # 新しい評価指標の追加フォーム
        st.markdown("## 新しい評価指標の追加")
        st.info("注意: 追加した評価指標は全てのマネージャーの評価に影響します。")
        
        with st.form("new_metric_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                metric_name = st.text_input(
                    "指標名",
                    help="1-100文字で入力してください"
                )
                metric_category = st.selectbox(
                    "カテゴリー",
                    ["custom", "core"],
                    help="core: 基本指標, custom: カスタム指標"
                )
            
            with col2:
                metric_weight = st.slider(
                    "重み付け",
                    min_value=0.1,
                    max_value=2.0,
                    value=1.0,
                    step=0.1,
                    help="指標の重要度を設定します（0.1: 最小 ～ 2.0: 最大）"
                )
            
            metric_desc = st.text_area(
                "説明",
                help="この評価指標が測定する能力や行動について説明してください"
            )
            
            submit_button = st.form_submit_button("追加", use_container_width=True)
            
            if submit_button:
                if not metric_name:
                    st.error("指標名を入力してください")
                elif not metric_desc:
                    st.error("説明を入力してください")
                else:
                    try:
                        db.add_evaluation_metric(
                            name=metric_name,
                            description=metric_desc,
                            category=metric_category,
                            weight=metric_weight
                        )
                        st.success(f"新しい評価指標「{metric_name}」を追加しました！")
                        st.balloons()
                        time.sleep(1)  # アニメーション効果のため少し待機
                        st.experimental_rerun()
                    except ValueError as e:
                        st.error(f"入力エラー: {str(e)}")
                    except RuntimeError as e:
                        st.error(f"システムエラー: {str(e)}")
                        st.error("管理者に連絡してください")
                    except Exception as e:
                        st.error(f"予期せぬエラーが発生しました: {str(e)}")
                        st.error("管理者に連絡してください")
                        
    except Exception as e:
        st.error("評価指標の表示中にエラーが発生しました")
        st.error(f"エラー詳細: {str(e)}")


# サイドバーナビゲーション
pages = {
    "ホーム": "home",
    "マネージャー一覧": "managers",
    "部門別分析": "department",
    "評価指標管理": "metrics"
}
page = st.sidebar.radio("ページ選択", list(pages.keys()))

if page == "ホーム":
    st.title("マネージャースキル分析ダッシュボード")
    st.write("マネージャーのスキル評価・育成支援のための分析ツールです。")

elif page == "マネージャー一覧":
    st.title("マネージャー一覧")
    managers_df = db.get_all_managers()
    components.display_manager_list(managers_df)

elif page == "部門別分析":
    st.title("部門別分析")
    
    try:
        # 部門別データの取得
        dept_df = db.get_department_analysis()
        
        if dept_df.empty:
            st.warning("分析可能なデータがありません")
        else:
            # 部門別比較レーダーチャート
            st.subheader("部門別スキルレーダーチャート")
            radar_chart = create_department_comparison_chart(dept_df)
            st.plotly_chart(radar_chart, use_container_width=True)
            
            # 部門別詳細比較
            st.subheader("部門別評価指標の詳細比較")
            metrics_chart = create_department_metrics_chart(dept_df)
            st.plotly_chart(metrics_chart, use_container_width=True)
            
            # 部門別データテーブル
            st.subheader("部門別データ一覧")
            formatted_df = dept_df.copy()
            formatted_df.columns = [
                '部門', 'マネージャー数', 'コミュニケーション', 'サポート',
                '目標管理', 'リーダーシップ', '問題解決力', '戦略'
            ]
            st.dataframe(
                formatted_df.style.format({
                    col: '{:.2f}' for col in formatted_df.columns[2:]
                }),
                use_container_width=True
            )
            
    except Exception as e:
        st.error("部門別分析の表示中にエラーが発生しました")
        st.error(f"エラー詳細: {str(e)}")