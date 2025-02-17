from openai import OpenAI
import os
import streamlit as st
from typing import Dict, Optional, Tuple
import json
from datetime import datetime, timedelta
import pandas as pd
import logging
from sqlalchemy import create_engine, text

# ロギング設定の初期化
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class AIAdvisor:
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI APIキーが設定されていません")
        
        self.client = OpenAI(api_key=api_key)
        self.debug_mode = os.getenv('DEBUG', '').lower() == 'true'
        
        # データベース接続の初期化
        from sqlalchemy import create_engine, text
        import pandas as pd
        import logging
        
        self.engine = create_engine(os.environ['DATABASE_URL'])
        
        # テーブルの作成
        with self.engine.connect() as conn:
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS ai_suggestion_history (
                    id SERIAL PRIMARY KEY,
                    manager_id INTEGER NOT NULL,
                    suggestion_text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_implemented BOOLEAN DEFAULT FALSE,
                    implementation_date TIMESTAMP,
                    effectiveness_rating INTEGER CHECK (effectiveness_rating BETWEEN 1 AND 5),
                    feedback_text TEXT
                );
            '''))
            conn.commit()
        
        # セッションステートの初期化
        if 'ai_cache' not in st.session_state:
            st.session_state.ai_cache = {}
        if 'api_calls_count' not in st.session_state:
            st.session_state.api_calls_count = 0
        if 'ai_model' not in st.session_state:
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            st.session_state.ai_model = 'gpt-3.5-turbo'
        
        # キャッシュ設定
        self.cache_expiry = timedelta(hours=24)  # キャッシュの有効期限を24時間に設定

    def _get_cache_key(self, scores: Dict[str, float]) -> str:
        """スコアから一意のキャッシュキーを生成"""
        sorted_scores = sorted(scores.items())
        return json.dumps(sorted_scores)

    def _clean_expired_cache(self):
        """期限切れのキャッシュエントリを削除"""
        now = datetime.now()
        expired_keys = []
        for key, (_, expires_at) in st.session_state.ai_cache.items():
            if now > expires_at:
                expired_keys.append(key)
        for key in expired_keys:
            del st.session_state.ai_cache[key]

    @property
    def cache_stats(self):
        """キャッシュの統計情報を取得"""
        return {
            'total_entries': len(st.session_state.ai_cache),
            'valid_entries': len([1 for _, (_, exp) in st.session_state.ai_cache.items() 
                                if exp > datetime.now()]),
            'expired_entries': len([1 for _, (_, exp) in st.session_state.ai_cache.items() 
                                if exp <= datetime.now()])
        }

    def clear_cache(self):
        """キャッシュをクリア"""
        st.session_state.ai_cache = {}

    def save_suggestion(self, manager_id: Optional[int], suggestion_text: str):
        """AIの提案を履歴として保存"""
        try:
            if not suggestion_text or not suggestion_text.strip():
                raise ValueError("提案テキストが空です")

            with self.engine.connect() as conn:
                query = """
                    INSERT INTO ai_suggestion_history (manager_id, suggestion_text)
                    VALUES (:manager_id, :suggestion_text)
                    RETURNING id;
                """
                result = conn.execute(text(query), {
                    'manager_id': manager_id,
                    'suggestion_text': suggestion_text.strip()
                })
                conn.commit()
                return result.scalar()
        except Exception as e:
            logging.error(f"提案の保存中にエラーが発生: {str(e)}")
            raise ValueError(f"提案の保存に失敗しました: {str(e)}")

    def get_suggestion_history(self, manager_id: int) -> pd.DataFrame:
        """特定のマネージャーのAI提案履歴を取得"""
        try:
            query = text('''
                SELECT 
                    id,
                    suggestion_text,
                    created_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Tokyo' as created_at,
                    is_implemented,
                    CASE 
                        WHEN implementation_date IS NOT NULL 
                        THEN implementation_date AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Tokyo'
                        ELSE NULL 
                    END as implementation_date,
                    effectiveness_rating,
                    feedback_text
                FROM ai_suggestion_history
                WHERE manager_id = :manager_id
                ORDER BY created_at DESC;
            ''')
            
            return pd.read_sql_query(
                query,
                self.engine,
                params={'manager_id': manager_id}
            )
        except Exception as e:
            logging.error(f"提案履歴の取得中にエラーが発生: {str(e)}")
            return pd.DataFrame()  # エラー時は空のDataFrameを返す

    def update_suggestion_status(
        self, 
        suggestion_id: int, 
        is_implemented: bool = None, 
        effectiveness_rating: int = None,
        feedback_text: str = None
    ):
        """AI提案の実装状態と効果を更新"""
        try:
            with self.engine.connect() as conn:
                update_dict = {}
                if is_implemented is not None:
                    update_dict['is_implemented'] = is_implemented
                    if is_implemented:
                        update_dict['implementation_date'] = datetime.now()
                if effectiveness_rating is not None:
                    update_dict['effectiveness_rating'] = effectiveness_rating
                if feedback_text is not None:
                    update_dict['feedback_text'] = feedback_text

                if update_dict:
                    query = """
                        UPDATE ai_suggestion_history
                        SET {}
                        WHERE id = :suggestion_id;
                    """.format(
                        ', '.join(f"{k} = :{k}" for k in update_dict.keys())
                    )
                    update_dict['suggestion_id'] = suggestion_id
                    conn.execute(text(query), update_dict)
                    conn.commit()
        except Exception as e:
            logging.error(f"提案状態の更新中にエラーが発生: {str(e)}")
            raise

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

    def get_prompt_templates(self) -> pd.DataFrame:
        """利用可能なプロンプトテンプレートを取得"""
        try:
            query = """
            SELECT id, name, description, template_text
            FROM ai_prompt_templates
            WHERE is_active = true
            ORDER BY name;
            """
            return pd.read_sql_query(query, self.engine)
        except Exception as e:
            logging.error(f"プロンプトテンプレート取得エラー: {str(e)}")
            return pd.DataFrame()

    def add_prompt_template(self, name: str, description: str, template_text: str) -> int:
        """新しいプロンプトテンプレートを追加"""
        try:
            query = """
            INSERT INTO ai_prompt_templates (name, description, template_text)
            VALUES (:name, :description, :template_text)
            RETURNING id;
            """
            with self.engine.connect() as conn:
                result = conn.execute(text(query), {
                    'name': name,
                    'description': description,
                    'template_text': template_text
                })
                conn.commit()
                return result.scalar()
        except Exception as e:
            logging.error(f"プロンプトテンプレート追加エラー: {str(e)}")
            raise

    def update_prompt_template(self, template_id: int, name: str, description: str, template_text: str):
        """プロンプトテンプレートを更新"""
        try:
            query = """
            UPDATE ai_prompt_templates
            SET name = :name,
                description = :description,
                template_text = :template_text,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :template_id;
            """
            with self.engine.connect() as conn:
                conn.execute(text(query), {
                    'template_id': template_id,
                    'name': name,
                    'description': description,
                    'template_text': template_text
                })
                conn.commit()
        except Exception as e:
            logging.error(f"プロンプトテンプレート更新エラー: {str(e)}")
            raise

    def generate_improvement_suggestions(self, scores: Dict[str, float], template_id: Optional[int] = None) -> str:
        """改善提案を生成（キャッシュ、デバッグモード、API制限付き）"""
        try:
            # APIコール回数制限チェック
            MAX_API_CALLS = 50  # 1セッションあたりの最大API呼び出し回数
            if st.session_state.api_calls_count >= MAX_API_CALLS:
                return "API呼び出し回数の制限に達しました。しばらく時間をおいて再度お試しください。"

            # デバッグモードチェック
            if self.debug_mode:
                return self._get_debug_response(scores)

            # キャッシュのクリーニングと確認
            self._clean_expired_cache()
            cache_key = f"{self._get_cache_key(scores)}_{template_id}"
            if cache_key in st.session_state.ai_cache:
                suggestion, expires_at = st.session_state.ai_cache[cache_key]
                if datetime.now() <= expires_at:
                    return suggestion

            # テンプレートの取得
            if template_id:
                query = "SELECT template_text FROM ai_prompt_templates WHERE id = :template_id;"
                with self.engine.connect() as conn:
                    result = conn.execute(text(query), {'template_id': template_id})
                    template = result.scalar()
                if template:
                    prompt = template.format(scores=scores)
                else:
                    template_id = None  # テンプレートが見つからない場合はデフォルトを使用

            # デフォルトテンプレート
            if not template_id:
                prompt = f"""
以下のマネージャーの評価スコアに基づいて改善提案を行ってください：
- コミュニケーション・フィードバック: {scores.get('communication', 0)}/5
- サポート・エンパワーメント: {scores.get('support', 0)}/5
- 目標管理・成果達成: {scores.get('goal_management', 0)}/5
- リーダーシップ・意思決定: {scores.get('leadership', 0)}/5
- 問題解決力: {scores.get('problem_solving', 0)}/5
- 戦略・成長支援: {scores.get('strategy', 0)}/5

特に低いスコアの領域に焦点を当て、具体的で実行可能な改善提案を提供してください。
マネジメントスキル向上のための実践的なステップを含めてください。
レスポンスは日本語でお願いします。
"""

            response = self.client.chat.completions.create(
                model=st.session_state.ai_model,
                messages=[
                    {"role": "system", "content": "あなたは経験豊富なマネジメントコーチとして、実践的なアドバイスを提供します。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            suggestion = response.choices[0].message.content
            if not suggestion:
                raise ValueError("AIからの応答が空でした")

            # キャッシュに保存（有効期限付き）
            expires_at = datetime.now() + self.cache_expiry
            st.session_state.ai_cache[cache_key] = (suggestion, expires_at)
            # API呼び出し回数をインクリメント
            st.session_state.api_calls_count += 1
            
            return suggestion
        except Exception as e:
            error_msg = f"AI提案生成エラー: {str(e)}"
            print(error_msg)  # ログ用
            return "AI提案の生成中にエラーが発生しました。しばらく時間をおいて再度お試しください。"
