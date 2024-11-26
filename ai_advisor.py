from openai import OpenAI
import os
import streamlit as st
from typing import Dict, Optional
import json

class AIAdvisor:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.debug_mode = os.getenv('DEBUG', '').lower() == 'true'
        
        # セッションステートの初期化
        if 'ai_cache' not in st.session_state:
            st.session_state.ai_cache = {}
        if 'api_calls_count' not in st.session_state:
            st.session_state.api_calls_count = 0
        if 'ai_model' not in st.session_state:
            st.session_state.ai_model = 'gpt-4'
        
        # サイドバーにモデル選択UIを追加（デフォルト値を変更）
        st.sidebar.subheader("AI設定")
        st.session_state.ai_model = st.sidebar.selectbox(
            "言語モデルの選択",
            options=['gpt-4', 'gpt-3.5-turbo'],  # デフォルト値を最初に配置
            help="より高度な提案にはGPT-4を、より速い応答にはGPT-3.5を選択してください。"
        )

    def _get_cache_key(self, scores: Dict[str, float]) -> str:
        """スコアから一意のキャッシュキーを生成"""
        sorted_scores = sorted(scores.items())
        return json.dumps(sorted_scores)

    def _get_debug_response(self, scores: Dict[str, float]) -> str:
        """デバッグモード用のダミーレスポンスを生成"""
        lowest_score = min(scores.values())
        lowest_skills = [k for k, v in scores.items() if v == lowest_score]
        
        return f"""デバッグモード: 改善提案
最も注力すべき領域: {', '.join(lowest_skills)}
スコア: {lowest_score}/5

1. 定期的な1on1ミーティングの実施
2. 具体的なフィードバックの提供
3. 目標設定と進捗管理の改善
4. チーム内コミュニケーションの活性化

これはデバッグモードでの表示です。実際のAPI呼び出しは行われていません。"""

    def generate_improvement_suggestions(self, scores: Dict[str, float]) -> str:
        """改善提案を生成（キャッシュ、デバッグモード、API制限付き）"""
        # APIコール回数制限チェック
        MAX_API_CALLS = 50  # 1セッションあたりの最大API呼び出し回数
        if st.session_state.api_calls_count >= MAX_API_CALLS:
            return "API呼び出し回数の制限に達しました。しばらく時間をおいて再度お試しください。"

        # デバッグモードチェック
        if self.debug_mode:
            return self._get_debug_response(scores)

        # キャッシュチェック
        cache_key = self._get_cache_key(scores)
        if cache_key in st.session_state.ai_cache:
            return st.session_state.ai_cache[cache_key]

        # AI提案生成
        prompt = f"""
以下のマネージャーの評価スコアに基づいて改善提案を行ってください：
- コミュニケーション・フィードバック: {scores['communication']}/5
- サポート・エンパワーメント: {scores['support']}/5
- 目標管理・成果達成: {scores['goal_management']}/5
- リーダーシップ・意思決定: {scores['leadership']}/5
- 問題解決力: {scores['problem_solving']}/5
- 戦略・成長支援: {scores['strategy']}/5

特に低いスコアの領域に焦点を当て、具体的で実行可能な改善提案を提供してください。
マネジメントスキル向上のための実践的なステップを含めてください。
"""

        try:
            response = self.client.chat.completions.create(
                model=st.session_state.ai_model,
                messages=[
                    {"role": "system", "content": "あなたは経験豊富なマネジメントコーチとして、実践的なアドバイスを提供します。"},
                    {"role": "user", "content": prompt}
                ]
            )
            
            suggestion = response.choices[0].message.content
            # キャッシュに保存
            st.session_state.ai_cache[cache_key] = suggestion
            # API呼び出し回数をインクリメント
            st.session_state.api_calls_count += 1
            
            return suggestion
        except Exception as e:
            print(f"AI提案生成エラー: {str(e)}")
            return "AI提案の生成中にエラーが発生しました。"
