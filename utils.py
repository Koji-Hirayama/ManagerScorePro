def calculate_company_average(managers_df):
    avg_scores = {
        'communication': managers_df['avg_communication'].mean(),
        'support': managers_df['avg_support'].mean(),
        'goal_management': managers_df['avg_goal'].mean(),
        'leadership': managers_df['avg_leadership'].mean(),
        'problem_solving': managers_df['avg_problem'].mean(),
        'strategy': managers_df['avg_strategy'].mean()
    }
    return avg_scores

def format_scores_for_ai(scores):
    return {
        'communication': scores['communication_score'],
        'support': scores['support_score'],
        'goal_management': scores['goal_management_score'],
        'leadership': scores['leadership_score'],
        'problem_solving': scores['problem_solving_score'],
        'strategy': scores['strategy_score']
    }
