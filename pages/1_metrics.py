import streamlit as st
import time
from database import DatabaseManager

st.title("評価指標設定")

try:
    # Initialize database
    db = DatabaseManager()
    
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
                    time.sleep(1)
                    st.experimental_rerun()
                except ValueError as e:
                    st.error(f"入力エラー: {str(e)}")
                except Exception as e:
                    st.error(f"予期せぬエラーが発生しました: {str(e)}")
                    st.error("管理者に連絡してください")
                    
except Exception as e:
    st.error("評価指標の表示中にエラーが発生しました")
    st.error(f"エラー詳細: {str(e)}")
