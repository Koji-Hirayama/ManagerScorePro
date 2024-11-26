import plotly.graph_objects as go
import pandas as pd

def create_radar_chart(scores, title="マネージャースキル評価"):
    categories = ['コミュニケーション・\nフィードバック',
                 'サポート・\nエンパワーメント',
                 '目標管理・成果達成',
                 'リーダーシップ・\n意思決定',
                 '問題解決力',
                 '戦略・成長支援']

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=scores,
        theta=categories,
        fill='toself',
        name=title
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5]
            )),
        showlegend=False,
        title=title
    )

    return fig

def create_trend_chart(history_df):
    fig = go.Figure()
    
    metrics = ['communication_score', 'support_score', 'goal_management_score',
               'leadership_score', 'problem_solving_score', 'strategy_score']
    
    for metric in metrics:
        fig.add_trace(go.Scatter(
            x=history_df['evaluation_date'],
            y=history_df[metric],
            name=metric.replace('_score', '').title(),
            mode='lines+markers'
        ))
    
    fig.update_layout(
        title="スキル評価の推移",
        xaxis_title="評価日",
        yaxis_title="スコア",
        yaxis_range=[0, 5]
    )
    
    return fig
