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

    def __del__(self):
        """デストラクタ：エンジンの破棄"""
        if hasattr(self, 'engine'):
            self.engine.dispose()