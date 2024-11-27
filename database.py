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

    def get_manager_details(self, manager_id):
        try:
            query = '''
                SELECT 
                    m.id,
                    m.name,
                    m.department,
                    e.evaluation_date,
                    e.communication_score,
                    e.support_score,
                    e.goal_management_score,
                    e.leadership_score,
                    e.problem_solving_score,
                    e.strategy_score
                FROM managers m
                LEFT JOIN evaluations e ON m.id = e.manager_id
                WHERE m.id = %(manager_id)s
                ORDER BY e.evaluation_date DESC;
            '''
            return pd.read_sql(query, self.engine, params={'manager_id': manager_id})
        except Exception as e:
            logging.error(f"マネージャー詳細データ取得エラー: {str(e)}")
            raise RuntimeError("マネージャー詳細の取得中にエラーが発生しました")

    def analyze_growth(self, manager_id):
        """マネージャーの成長率を分析"""
        try:
            query = '''
                WITH evaluation_periods AS (
                    SELECT 
                        manager_id,
                        evaluation_date,
                        (communication_score + support_score + goal_management_score + 
                         leadership_score + problem_solving_score + strategy_score) / 6.0 as avg_score,
                        LAG((communication_score + support_score + goal_management_score + 
                            leadership_score + problem_solving_score + strategy_score) / 6.0) 
                        OVER (PARTITION BY manager_id ORDER BY evaluation_date) as prev_score
                    FROM evaluations
                    WHERE manager_id = %(manager_id)s
                    ORDER BY evaluation_date DESC
                )
                SELECT 
                    evaluation_date,
                    avg_score,
                    CASE 
                        WHEN prev_score IS NOT NULL 
                        THEN ((avg_score - prev_score) / prev_score * 100)
                        ELSE 0 
                    END as growth_rate
                FROM evaluation_periods;
            '''
            return pd.read_sql(query, self.engine, params={'manager_id': manager_id})
        except Exception as e:
            logging.error(f"成長分析データ取得エラー: {str(e)}")
            return pd.DataFrame()  # エラー時は空のDataFrameを返す

    def get_department_analysis(self):
        """部門別の評価スコアを取得"""
        try:
            query = '''
                WITH latest_evaluations AS (
                    SELECT 
                        manager_id,
                        MAX(evaluation_date) as latest_date
                    FROM evaluations
                    GROUP BY manager_id
                )
                SELECT 
                    m.department,
                    COUNT(DISTINCT m.id) as manager_count,
                    AVG(e.communication_score) as avg_communication,
                    AVG(e.support_score) as avg_support,
                    AVG(e.goal_management_score) as avg_goal,
                    AVG(e.leadership_score) as avg_leadership,
                    AVG(e.problem_solving_score) as avg_problem,
                    AVG(e.strategy_score) as avg_strategy
                FROM managers m
                JOIN latest_evaluations le ON m.id = le.manager_id
                JOIN evaluations e ON m.id = e.manager_id 
                    AND e.evaluation_date = le.latest_date
                GROUP BY m.department
                ORDER BY m.department;
            '''
            return pd.read_sql(query, self.engine)
        except Exception as e:
            logging.error(f"部門別分析データ取得エラー: {str(e)}")
            return pd.DataFrame()  # エラー時は空のDataFrameを返す
    def __del__(self):
        """デストラクタ：エンジンの破棄"""
        if hasattr(self, 'engine'):
            self.engine.dispose()

    def get_all_managers(self):
        try:
            query = '''
                SELECT 
                    m.*,
                    AVG(e.communication_score) as avg_communication,
                    AVG(e.support_score) as avg_support,
                    AVG(e.goal_management_score) as avg_goal,
                    AVG(e.leadership_score) as avg_leadership,
                    AVG(e.problem_solving_score) as avg_problem,
                    AVG(e.strategy_score) as avg_strategy
                FROM managers m
                LEFT JOIN evaluations e ON m.id = e.manager_id
                GROUP BY m.id, m.name, m.department
                ORDER BY m.name
            '''
            return pd.read_sql(query, self.engine)
        except Exception as e:
            logging.error(f"マネージャー一覧取得エラー: {str(e)}")
            return pd.DataFrame()

    def get_department_statistics(self):
        """部門別の評価統計を取得"""
        try:
            query = """
            SELECT 
                department,
                COUNT(DISTINCT m.id) as manager_count,
                AVG(communication_score) as avg_communication,
                AVG(support_score) as avg_support,
                AVG(goal_management_score) as avg_goal,
                AVG(leadership_score) as avg_leadership,
                AVG(problem_solving_score) as avg_problem,
                AVG(strategy_score) as avg_strategy
            FROM managers m
            JOIN evaluations e ON m.id = e.manager_id
            GROUP BY department
            """
            return pd.read_sql(query, self.engine)
        except Exception as e:
            print(f"部門別統計取得エラー: {str(e)}")
            return pd.DataFrame()

            self.engine.dispose()
def generate_sample_data(self):
    def execute_query(self, query: str, params: dict = None) -> list:
        """SQLクエリを実行し、結果を辞書のリストとして返す"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query), params or {})
                return [dict(row) for row in result]
        except Exception as e:
            logging.error(f"クエリ実行エラー: {str(e)}")
            return []

    import random
    from datetime import datetime, timedelta
    
    try:
        # 会社規模の設定（100-500人）
        company_size = random.randint(100, 500)
        manager_count = int(company_size * random.uniform(0.1, 0.2))  # 10-20%をマネージャーに
        
        # 部門の設定
        departments = ['営業', '開発', '人事', '経営企画', 'カスタマーサクセス', 'マーケティング']
        
        # マネージャーデータの生成
        for i in range(manager_count):
            # マネージャー基本情報
            manager_name = f"サンプルマネージャー{i+1}"
            department = random.choice(departments)
            
            # マネージャーの追加
            manager_id = self.add_manager(manager_name, department)
            
            # 過去6ヶ月分の評価データを生成
            for months_ago in range(6):
                eval_date = datetime.now() - timedelta(days=30*months_ago)
                
                # 基本スコアを設定（3.0-4.5の範囲）
                base_score = random.uniform(3.0, 4.5)
                
                # 各項目のスコアを生成（基本スコアの±0.5の範囲）
                self.add_evaluation(
                    manager_id=manager_id,
                    evaluation_date=eval_date,
                    scores={
                        'communication': max(1, min(5, base_score + random.uniform(-0.5, 0.5))),
                        'support': max(1, min(5, base_score + random.uniform(-0.5, 0.5))),
                        'goal_management': max(1, min(5, base_score + random.uniform(-0.5, 0.5))),
                        'leadership': max(1, min(5, base_score + random.uniform(-0.5, 0.5))),
                        'problem_solving': max(1, min(5, base_score + random.uniform(-0.5, 0.5))),
                        'strategy': max(1, min(5, base_score + random.uniform(-0.5, 0.5)))
                    }
                )
        
        return True
    except Exception as e:
        logging.error(f"サンプルデータ生成エラー: {str(e)}")
        return False