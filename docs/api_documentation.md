# API ドキュメント

## データベース API

### DatabaseManager クラス

#### メソッド一覧

1. get_all_managers()
   - 説明: 全マネージャーの情報を取得
   - 戻り値: pandas DataFrame
   - カラム: id, name, department, avg_scores

2. get_manager_details(manager_id: int)
   - 説明: 特定のマネージャーの詳細情報を取得
   - パラメータ: manager_id (int)
   - 戻り値: pandas DataFrame

3. get_department_statistics()
   - 説明: 部門別の統計情報を取得
   - 戻り値: pandas DataFrame
   - 統計情報: 平均スコア、マネージャー数

4. analyze_growth(manager_id: int)
   - 説明: マネージャーの成長率を分析
   - パラメータ: manager_id (int)
   - 戻り値: pandas DataFrame（月次成長率）

## AI アドバイザー API

### AIAdvisor クラス

#### メソッド一覧

1. generate_improvement_suggestions(scores: Dict[str, float])
   - 説明: スコアに基づく改善提案を生成
   - パラメータ: scores (Dict[str, float])
   - 戻り値: str（提案テキスト）

2. save_suggestion(manager_id: int, suggestion_text: str)
   - 説明: AI提案を履歴として保存
   - パラメータ:
     - manager_id: int
     - suggestion_text: str
   - 戻り値: int（提案ID）

3. get_suggestion_history(manager_id: int)
   - 説明: 提案履歴を取得
   - パラメータ: manager_id (int)
   - 戻り値: pandas DataFrame

## 可視化 API

### 関数一覧

1. create_radar_chart(scores, title="マネージャースキル評価")
   - 説明: スキル評価のレーダーチャートを作成
   - パラメータ:
     - scores: List[float]
     - title: str
   - 戻り値: plotly.graph_objects.Figure

2. create_trend_chart(history_df)
   - 説明: スキル評価の推移チャートを作成
   - パラメータ: history_df (pandas DataFrame)
   - 戻り値: plotly.graph_objects.Figure

3. create_department_comparison_chart(dept_df)
   - 説明: 部門別比較チャートを作成
   - パラメータ: dept_df (pandas DataFrame)
   - 戻り値: plotly.graph_objects.Figure
