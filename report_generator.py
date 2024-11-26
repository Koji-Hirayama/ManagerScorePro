import pandas as pd
from datetime import datetime
import streamlit as st
from ai_advisor import AIAdvisor
from utils import format_scores_for_ai

def generate_manager_report(manager_data, growth_data, ai_advisor):
    """マネージャーの評価レポートを生成"""
    if manager_data.empty:
        return None
        
    latest_scores = manager_data.iloc[0]
    
    # 基本情報セクション
    report = f"""
# マネージャー評価レポート
生成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}

## 基本情報
- 名前: {latest_scores['name']}
- 部門: {latest_scores['department']}

## 現在の評価スコア
| 評価項目 | スコア |
|----------|--------|
| コミュニケーション | {latest_scores['communication_score']:.1f}/5.0 |
| サポート | {latest_scores['support_score']:.1f}/5.0 |
| 目標管理 | {latest_scores['goal_management_score']:.1f}/5.0 |
| リーダーシップ | {latest_scores['leadership_score']:.1f}/5.0 |
| 問題解決力 | {latest_scores['problem_solving_score']:.1f}/5.0 |
| 戦略 | {latest_scores['strategy_score']:.1f}/5.0 |

## 総合評価
総合スコア: {calculate_overall_score(latest_scores):.1f}/5.0
"""

    # 成長分析セクション
    if not growth_data.empty:
        latest_growth = growth_data.iloc[0]['growth_rate']
        avg_growth = growth_data['growth_rate'].mean()
        
        report += f"""
## 成長分析
- 直近の成長率: {latest_growth:.1f}%
- 平均成長率: {avg_growth:.1f}%
"""

    # AI提案セクション
    if ai_advisor:
        try:
            individual_scores = format_scores_for_ai(latest_scores)
            ai_suggestions = ai_advisor.generate_improvement_suggestions(individual_scores)
            report += f"""
## AI改善提案
{ai_suggestions}
"""
        except Exception as e:
            report += "\n## AI改善提案\nAI提案の生成中にエラーが発生しました。"

    return report

def calculate_overall_score(scores):
    """総合評価スコアを計算"""
    eval_scores = [
        scores['communication_score'],
        scores['support_score'],
        scores['goal_management_score'],
        scores['leadership_score'],
        scores['problem_solving_score'],
        scores['strategy_score']
    ]
    return sum(eval_scores) / len(eval_scores)

def export_report_to_markdown(report_content, filename):
    """レポートをMarkdownファイルとして保存"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_content)
        return True
    except Exception as e:
        st.error(f"レポートの保存中にエラーが発生しました: {str(e)}")
        return False
