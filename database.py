from sqlalchemy import create_engine, exc
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import sessionmaker
import pandas as pd
import os
from datetime import datetime, timedelta
import logging

class DatabaseManager:
    def __init__(self):
        self.db_url = os.environ['DATABASE_URL']
        self._setup_engine()
        self._setup_logging()

    def _setup_engine(self):
        """SQLAlchemy engineのセットアップ"""
        try:
            self.engine = create_engine(
                self.db_url,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800
            )
            self.Session = sessionmaker(bind=self.engine)
            logging.info("データベース接続プールを初期化しました")
        except Exception as e:
            logging.error(f"データベース接続エラー: {str(e)}")
            raise

    def _setup_logging(self):
        """ロギングの設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def get_evaluation_metrics(self):
        """有効な評価指標を取得"""
        try:
            query = """
            SELECT id, name, description, category, weight
            FROM evaluation_metrics
            WHERE is_active = true
            ORDER BY category, id;
            """
            return pd.read_sql(query, self.engine)
        except exc.SQLAlchemyError as e:
            logging.error(f"評価指標取得エラー: {str(e)}")
            raise RuntimeError("評価指標の取得中にデータベースエラーが発生しました")
        except Exception as e:
            logging.error(f"予期せぬエラー: {str(e)}")
            raise

    def add_evaluation_metric(self, name, description, category='custom', weight=1.0):
        """新しい評価指標を追加"""
        session = self.Session()
        try:
            # 入力値の検証
            if not name or len(name) > 100:
                raise ValueError("指標名は1-100文字で入力してください")
            if not description:
                raise ValueError("説明を入力してください")
            if weight < 0.1 or weight > 2.0:
                raise ValueError("重み付けは0.1から2.0の間で設定してください")
            if category not in ['core', 'custom']:
                raise ValueError("無効なカテゴリーです")

            # 重複チェック
            result = session.execute(
                "SELECT COUNT(*) FROM evaluation_metrics WHERE name = :name",
                {"name": name}
            ).scalar()
            if result > 0:
                raise ValueError(f"指標名「{name}」は既に存在します")

            # 新規指標の追加
            result = session.execute("""
                INSERT INTO evaluation_metrics (name, description, category, weight)
                VALUES (:name, :description, :category, :weight)
                RETURNING id;
            """, {
                "name": name,
                "description": description,
                "category": category,
                "weight": weight
            })
            
            new_id = result.scalar()
            session.commit()
            logging.info(f"新しい評価指標を追加しました: {name}")
            return new_id

        except exc.SQLAlchemyError as e:
            session.rollback()
            logging.error(f"データベースエラー: {str(e)}")
            raise RuntimeError("評価指標の追加中にデータベースエラーが発生しました")
        except ValueError as e:
            session.rollback()
            logging.warning(f"入力値エラー: {str(e)}")
            raise
        except Exception as e:
            session.rollback()
            logging.error(f"予期せぬエラー: {str(e)}")
            raise
        finally:
            session.close()

    def get_evaluation_metrics(self):
        """評価指標の一覧を取得"""
        try:
            query = '''
                SELECT 
                    id,
                    name,
                    description,
                    category,
                    weight
                FROM evaluation_metrics
                ORDER BY category, name;
            '''
            return pd.read_sql(query, self.engine)
        except Exception as e:
            logging.error(f"評価指標一覧取得エラー: {str(e)}")
            raise RuntimeError("評価指標一覧の取得中にエラーが発生しました")

    def add_evaluation_metric(self, name: str, description: str, category: str, weight: float):
        """新しい評価指標を追加"""
        try:
            query = '''
                INSERT INTO evaluation_metrics (name, description, category, weight)
                VALUES (%s, %s, %s, %s)
                RETURNING id;
            '''
            with self.engine.connect() as conn:
                result = conn.execute(text(query), [name, description, category, weight])
                conn.commit()
                return result.fetchone()[0]
        except Exception as e:
            logging.error(f"評価指標追加エラー: {str(e)}")
            raise RuntimeError("評価指標の追加中にエラーが発生しました")

    def get_all_managers(self):
        try:
            query = '''
                SELECT 
                    m.id,
                    m.name,
                    m.department,
                    AVG(e.communication_score) as avg_communication,
                    AVG(e.support_score) as avg_support,
                    AVG(e.goal_management_score) as avg_goal,
                    AVG(e.leadership_score) as avg_leadership,
                    AVG(e.problem_solving_score) as avg_problem,
                    AVG(e.strategy_score) as avg_strategy
                FROM managers m
                LEFT JOIN evaluations e ON m.id = e.manager_id
                GROUP BY m.id, m.name, m.department
                ORDER BY m.name;
            '''
            return pd.read_sql(query, self.engine)
        except Exception as e:
            logging.error(f"マネージャー一覧取得エラー: {str(e)}")
            raise RuntimeError("マネージャー一覧の取得中にエラーが発生しました")

    def __del__(self):
        """デストラクタ：エンジンの破棄"""
        if hasattr(self, 'engine'):
            self.engine.dispose()