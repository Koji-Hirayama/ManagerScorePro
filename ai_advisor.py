import openai
import os

class AIAdvisor:
    def __init__(self):
        openai.api_key = os.getenv('OPENAI_API_KEY')

    def generate_improvement_suggestions(self, scores: dict) -> str:
        prompt = f"""
        Given the following manager evaluation scores:
        - Communication & Feedback: {scores['communication']}/5
        - Support & Empowerment: {scores['support']}/5
        - Goal Management: {scores['goal_management']}/5
        - Leadership & Decision Making: {scores['leadership']}/5
        - Problem Solving: {scores['problem_solving']}/5
        - Strategy & Growth: {scores['strategy']}/5

        Please provide specific, actionable suggestions for improvement in the areas with lower scores.
        Focus on practical steps that can be taken to enhance management skills.
        """

        try:
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an experienced management coach providing actionable advice."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"AI提案生成エラー: {str(e)}")
            return "AI提案の生成中にエラーが発生しました。"
