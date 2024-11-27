from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from models import Base, AIModelConfig, CacheConfig
import pandas as pd
import logging
import os
from datetime import datetime, timedelta
import random

class DatabaseManager:
    def __init__(self):
        """データベース接続の初期化"""
        try:
            self.engine = create_engine(
                os.environ['DATABASE_URL'],
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10
            )
            Session = sessionmaker(bind=self.engine)
            self.Session = Session
            logging.info("データベース接続プールを初期化しました")
        except Exception as e:
            logging.error(f"データベース接続エラー: {str(e)}")
            raise

    def execute_query(self, query: str, params: dict = None) -> list:
        """SQLクエリを実行し、結果を辞書のリストとして返す"""
        try:
            with self.engine.connect() as conn:
                if params is None:
                    params = {}
                # パラメータが辞書でない場合は変換
                if not isinstance(params, dict):
                    params = dict(params)
                result = conn.execute(text(query), params)
                return [dict(row._mapping) for row in result]
        except Exception as e:
            logging.error(f"クエリ実行エラー: {str(e)}")
            raise

    def get_all_managers(self):
        """全マネージャーの情報を取得"""
        try:
            query = """
            WITH latest_scores AS (
                SELECT 
                    e.manager_id,
                    AVG(e.communication_score) as avg_communication,
                    AVG(e.support_score) as avg_support,
                    AVG(e.goal_management_score) as avg_goal,
                    AVG(e.leadership_score) as avg_leadership,
                    AVG(e.problem_solving_score) as avg_problem,
                    AVG(e.strategy_score) as avg_strategy
                FROM evaluations e
                WHERE e.evaluation_date >= NOW() - INTERVAL '6 months'
                GROUP BY e.manager_id
            )
            SELECT 
                m.id,
                m.name,
                m.department,
                COALESCE(ls.avg_communication, 0) as avg_communication,
                COALESCE(ls.avg_support, 0) as avg_support,
                COALESCE(ls.avg_goal, 0) as avg_goal,
                COALESCE(ls.avg_leadership, 0) as avg_leadership,
                COALESCE(ls.avg_problem, 0) as avg_problem,
                COALESCE(ls.avg_strategy, 0) as avg_strategy
            FROM managers m
            LEFT JOIN latest_scores ls ON m.id = ls.manager_id
            ORDER BY m.name;
            """
            return pd.read_sql_query(query, self.engine)
        except Exception as e:
            logging.error(f"マネージャー情報の取得中にエラーが発生: {str(e)}")
            return pd.DataFrame()

    def get_manager_details(self, manager_id: int):
        """特定のマネージャーの詳細情報を取得"""
        if not isinstance(manager_id, int):
            logging.error("無効なmanager_id形式です")
            return pd.DataFrame()

        try:
            # まずマネージャーの存在確認
            check_query = "SELECT COUNT(*) FROM managers WHERE id = %(manager_id)s"
            with self.engine.connect() as conn:
                result = conn.execute(text(check_query), {'manager_id': manager_id})
                if result.scalar() == 0:
                    logging.error(f"指定されたID {manager_id} のマネージャーが見つかりません")
                    return pd.DataFrame()

            query = """
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
            """
            df = pd.read_sql_query(
                query,
                self.engine,
                params={'manager_id': manager_id}
            )
            
            if df.empty:
                logging.info(f"マネージャー (ID: {manager_id}) の評価データが存在しません")
            return df

        except Exception as e:
            logging.error(f"マネージャー詳細の取得中にエラーが発生: {str(e)}")
            if "no such column" in str(e).lower():
                logging.error("データベーススキーマが正しくありません")
            elif "operational error" in str(e).lower():
                logging.error("データベース接続エラーが発生しました")
            return pd.DataFrame()

    def get_department_statistics(self):
        """部門別の統計情報を取得"""
        try:
            query = """
            WITH recent_evals AS (
                SELECT 
                    m.department,
                    AVG(e.communication_score) as avg_communication,
                    AVG(e.support_score) as avg_support,
                    AVG(e.goal_management_score) as avg_goal,
                    AVG(e.leadership_score) as avg_leadership,
                    AVG(e.problem_solving_score) as avg_problem,
                    AVG(e.strategy_score) as avg_strategy,
                    COUNT(DISTINCT m.id) as manager_count
                FROM managers m
                LEFT JOIN evaluations e ON m.id = e.manager_id
                WHERE e.evaluation_date >= NOW() - INTERVAL '3 months'
                GROUP BY m.department
            )
            SELECT *,
                (avg_communication + avg_support + avg_goal + 
                 avg_leadership + avg_problem + avg_strategy) / 6 as overall_avg
            FROM recent_evals
            ORDER BY overall_avg DESC;
            """
            return pd.read_sql_query(query, self.engine)
        except Exception as e:
            logging.error(f"部門統計の取得中にエラーが発生: {str(e)}")
            return pd.DataFrame()

    def get_evaluation_metrics(self):
        """評価指標の一覧を取得"""
        try:
            query = """
            SELECT *
            FROM evaluation_metrics
            ORDER BY category, name;
            """
            return pd.read_sql_query(query, self.engine)
        except Exception as e:
            logging.error(f"評価指標の取得中にエラーが発生: {str(e)}")
            return pd.DataFrame()

    def add_manager(self, name: str, department: str) -> int:
        """新しいマネージャーを追加"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("""
                        INSERT INTO managers (name, department)
                        VALUES (:name, :department)
                        RETURNING id;
                    """),
                    {'name': name, 'department': department}
                )
                manager_id = result.scalar()
                conn.commit()
                return manager_id
        except Exception as e:
            logging.error(f"マネージャー追加エラー: {str(e)}")
            raise

    def add_evaluation(self, manager_id: int, evaluation_date: datetime, scores: dict):
        """評価スコアを追加"""
        try:
            with self.engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO evaluations (
                            manager_id,
                            evaluation_date,
                            communication_score,
                            support_score,
                            goal_management_score,
                            leadership_score,
                            problem_solving_score,
                            strategy_score
                        ) VALUES (
                            :manager_id,
                            :evaluation_date,
                            :communication,
                            :support,
                            :goal_management,
                            :leadership,
                            :problem_solving,
                            :strategy
                        );
                    """),
                    {
                        'manager_id': manager_id,
                        'evaluation_date': evaluation_date,
                        'communication': scores['communication'],
                        'support': scores['support'],
                        'goal_management': scores['goal_management'],
                        'leadership': scores['leadership'],
                        'problem_solving': scores['problem_solving'],
                        'strategy': scores['strategy']
                    }
                )
                conn.commit()
        except Exception as e:
            logging.error(f"評価スコア追加エラー: {str(e)}")
            raise

    def add_evaluation_metric(self, name: str, description: str, category: str, weight: float):
        """評価指標を追加"""
        try:
            with self.engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO evaluation_metrics (name, description, category, weight)
                        VALUES (:name, :description, :category, :weight);
                    """),
                    {
                        'name': name,
                        'description': description,
                        'category': category,
                        'weight': weight
                    }
                )
                conn.commit()
        except Exception as e:
            logging.error(f"評価指標追加エラー: {str(e)}")
            raise

    def analyze_growth(self, manager_id: int):
        """マネージャーの成長率を分析"""
        try:
            query = """
            WITH monthly_scores AS (
                SELECT 
                    DATE_TRUNC('month', evaluation_date) as month,
                    AVG((communication_score + support_score + goal_management_score + 
                         leadership_score + problem_solving_score + strategy_score) / 6) as avg_score
                FROM evaluations
                WHERE manager_id = :manager_id
                GROUP BY DATE_TRUNC('month', evaluation_date)
                ORDER BY month
            ),
            score_changes AS (
                SELECT 
                    month,
                    avg_score,
                    LAG(avg_score) OVER (ORDER BY month) as prev_score
                FROM monthly_scores
            )
            SELECT 
                month,
                avg_score,
                CASE 
                    WHEN prev_score IS NOT NULL AND prev_score != 0
                    THEN ((avg_score - prev_score) / prev_score * 100)
                    ELSE 0 
                END as growth_rate
            FROM score_changes
            ORDER BY month DESC;
            """
            return pd.read_sql_query(
                query,
                self.engine,
                params={'manager_id': manager_id}
            )
        except Exception as e:
            logging.error(f"成長分析エラー: {str(e)}")
            return pd.DataFrame()

    def generate_sample_data(self):
        """サンプルデータを生成"""
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

    def __del__(self):
        """デストラクタ：エンジンの破棄"""
        if hasattr(self, 'engine'):
            self.engine.dispose()