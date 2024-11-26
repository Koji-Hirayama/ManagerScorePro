import os
import psycopg2
import pandas as pd
from datetime import datetime, timedelta
from datetime import datetime, timedelta

class Database:
    def __init__(self):
        """データベース接続の初期化"""
        try:
            self.conn = psycopg2.connect(
                os.environ['DATABASE_URL']
            )
            print("データベース接続成功")
            self.create_tables()
            
            # データベースが空かチェックしてサンプルデータを投入
            if self.is_database_empty():
                print("データベースが空のため、サンプルデータを投入します")
                if self.insert_sample_data():
                    print("サンプルデータの投入が完了しました")
                else:
                    print("サンプルデータの投入に失敗しました")
        except Exception as e:
            print(f"データベース接続エラー: {str(e)}")
            raise

    def create_tables(self):
        """テーブルの作成"""
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS managers (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    department VARCHAR(100)
                );

                CREATE TABLE IF NOT EXISTS evaluations (
                    id SERIAL PRIMARY KEY,
                    manager_id INTEGER REFERENCES managers(id),
                    evaluation_date DATE DEFAULT CURRENT_DATE,
                    communication_score FLOAT,
                    support_score FLOAT,
                    goal_management_score FLOAT,
                    leadership_score FLOAT,
                    problem_solving_score FLOAT,
                    strategy_score FLOAT
                );
            """)
            self.conn.commit()

    def get_all_managers(self):
        """全マネージャーの最新の評価データを取得"""
        try:
            query = """
            SELECT 
                m.id,
                m.name,
                m.department,
                COALESCE(AVG(e.communication_score), 0) as avg_communication,
                COALESCE(AVG(e.support_score), 0) as avg_support,
                COALESCE(AVG(e.goal_management_score), 0) as avg_goal,
                COALESCE(AVG(e.leadership_score), 0) as avg_leadership,
                COALESCE(AVG(e.problem_solving_score), 0) as avg_problem,
                COALESCE(AVG(e.strategy_score), 0) as avg_strategy
            FROM managers m
            LEFT JOIN evaluations e ON m.id = e.manager_id
            GROUP BY m.id, m.name, m.department
            ORDER BY m.name
            """
            print("マネージャーデータを取得中...")
            df = pd.read_sql(query, self.conn)
            print(f"取得完了: {len(df)}件のマネージャーデータを取得")
            return df
        except Exception as e:
            print(f"マネージャーデータ取得エラー: {str(e)}")
            raise

    def is_database_empty(self):
        """データベースが空かどうかをチェック"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM managers")
                manager_count = cur.fetchone()[0]
                return manager_count == 0
        except Exception as e:
            print(f"データベース確認エラー: {str(e)}")
            return True

    def get_manager_details(self, manager_id):
        """特定のマネージャーの評価履歴を取得"""
        try:
            query = """
            SELECT 
                e.*,
                m.name,
                m.department
            FROM evaluations e
            JOIN managers m ON e.manager_id = m.id
            WHERE m.id = %s
            ORDER BY evaluation_date DESC
            """
            print(f"マネージャーID {manager_id} の詳細データを取得中...")
            df = pd.read_sql(query, self.conn, params=(manager_id,))
            print(f"取得完了: {len(df)}件の評価データを取得")
            return df
        except Exception as e:
            print(f"マネージャー詳細データ取得エラー: {str(e)}")
            raise

    def insert_sample_data(self):
        """サンプルデータを投入する関数"""
        try:
            with self.conn.cursor() as cur:
                # トランザクション開始
                cur.execute("BEGIN;")
                
                # マネージャーデータの投入
                managers = [
                    ('山田太郎', '営業部'),
                    ('鈴木花子', '開発部'),
                    ('佐藤健一', 'カスタマーサポート部'),
                    ('田中美咲', '人事部')
                ]
                
                manager_ids = []
                for name, dept in managers:
                    cur.execute(
                        "INSERT INTO managers (name, department) VALUES (%s, %s) RETURNING id;",
                        (name, dept)
                    )
                    manager_ids.append(cur.fetchone()[0])
                
                # 評価データの投入（過去3ヶ月分）
                for manager_id in manager_ids:
                    base_scores = {
                        'communication': round(3.0 + (manager_id % 2) * 0.5, 1),
                        'support': round(3.2 + (manager_id % 3) * 0.3, 1),
                        'goal_management': round(3.5 + (manager_id % 2) * 0.4, 1),
                        'leadership': round(3.3 + (manager_id % 3) * 0.2, 1),
                        'problem_solving': round(3.4 + (manager_id % 2) * 0.3, 1),
                        'strategy': round(3.1 + (manager_id % 3) * 0.4, 1)
                    }
                    
                    for month in range(3):
                        eval_date = datetime.now() - timedelta(days=30 * month)
                        growth_factor = month * 0.1  # 時間とともに少しずつ向上
                        
                        cur.execute("""
                            INSERT INTO evaluations 
                            (manager_id, evaluation_date, communication_score, support_score,
                             goal_management_score, leadership_score, problem_solving_score,
                             strategy_score)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                        """, (
                            manager_id,
                            eval_date.date(),
                            min(5.0, base_scores['communication'] + growth_factor),
                            min(5.0, base_scores['support'] + growth_factor),
                            min(5.0, base_scores['goal_management'] + growth_factor),
                            min(5.0, base_scores['leadership'] + growth_factor),
                            min(5.0, base_scores['problem_solving'] + growth_factor),
                            min(5.0, base_scores['strategy'] + growth_factor)
                        ))
                
                # トランザクションのコミット
                self.conn.commit()
                return True
                
        except Exception as e:
            # エラー発生時はロールバック
            self.conn.rollback()
            print(f"Error inserting sample data: {str(e)}")
            return False

    def __del__(self):
        """デストラクタ：接続のクローズ"""
        if hasattr(self, 'conn'):
            self.conn.close()