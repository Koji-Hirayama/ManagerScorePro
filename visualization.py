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


def create_growth_chart(history_df):
    """成長率の推移を可視化"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=history_df['evaluation_date'],
        y=history_df['growth_rate'],
        mode='lines+markers',
        name='成長率',
        line=dict(color='#2E8B57')
    ))
    
    fig.update_layout(
        title="成長率の推移",
        xaxis_title="評価日",
        yaxis_title="成長率 (%)",
        showlegend=True
    )
    
    return fig

def create_department_comparison_chart(dept_df):
    """部門別のスキル比較レーダーチャート"""
    categories = ['コミュニケーション', 'サポート', '目標管理',
                 'リーダーシップ', '問題解決力', '戦略']
    
    fig = go.Figure()
    
    for _, dept_data in dept_df.iterrows():
        department = dept_data['department']
        values = [
            dept_data['avg_communication'],
            dept_data['avg_support'],
            dept_data['avg_goal'],
            dept_data['avg_leadership'],
            dept_data['avg_problem'],
            dept_data['avg_strategy']
        ]
        # レーダーチャートのデータポイントを閉じるため、最初の値を最後にも追加
        values.append(values[0])
        categories_closed = categories + [categories[0]]
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories_closed,
            name=f"{department} (n={int(dept_data['manager_count'])})",
            fill='toself'
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5]
            )
        ),
        showlegend=True,
        title="部門別スキル比較"
    )
    
    return fig

def create_department_metrics_chart(dept_df):
    """部門別の各指標の棒グラフ"""
    metrics = {
        'avg_communication': 'コミュニケーション',
        'avg_support': 'サポート',
        'avg_goal': '目標管理',
        'avg_leadership': 'リーダーシップ',
        'avg_problem': '問題解決力',
        'avg_strategy': '戦略'
    }
    
    fig = go.Figure()
    
    for metric_key, metric_name in metrics.items():
        fig.add_trace(go.Bar(
            name=metric_name,
            x=dept_df['department'],
            y=dept_df[metric_key],
            text=dept_df[metric_key].round(2),
            textposition='auto',
        ))
    
    fig.update_layout(
        title="部門別評価指標の詳細比較",
        xaxis_title="部門",
        yaxis_title="平均スコア",
        barmode='group',
        yaxis_range=[0, 5]
    )
    
    return fig