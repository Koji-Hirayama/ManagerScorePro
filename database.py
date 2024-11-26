import os
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd

class Database:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv('PGHOST'),
            database=os.getenv('PGDATABASE'),
            user=os.getenv('PGUSER'),
            password=os.getenv('PGPASSWORD'),
            port=os.getenv('PGPORT')
        )
        self.create_tables()

    def create_tables(self):
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
        query = """
        SELECT m.*, 
               AVG(e.communication_score) as avg_communication,
               AVG(e.support_score) as avg_support,
               AVG(e.goal_management_score) as avg_goal,
               AVG(e.leadership_score) as avg_leadership,
               AVG(e.problem_solving_score) as avg_problem,
               AVG(e.strategy_score) as avg_strategy
        FROM managers m
        LEFT JOIN evaluations e ON m.id = e.manager_id
        GROUP BY m.id
        """
        return pd.read_sql(query, self.conn)

    def get_manager_details(self, manager_id):
        query = f"""
        SELECT * FROM evaluations
        WHERE manager_id = {manager_id}
        ORDER BY evaluation_date DESC
        """
        return pd.read_sql(query, self.conn)
