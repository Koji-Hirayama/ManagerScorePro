# セットアップガイド

## 1. 環境要件

### 必要なソフトウェア
- Python 3.11 以上
- PostgreSQL データベース
- OpenAI API アカウント

### 必要なパッケージ
- streamlit>=1.40.2
- pandas
- plotly>=2.2.3
- sqlalchemy>=2.0.36
- psycopg2-binary>=2.9.10
- openai>=1.55.1
- alembic

## 2. 初期セットアップ

### 環境変数の設定
```bash
# データベース接続情報
DATABASE_URL=postgresql://username:password@host:port/dbname

# OpenAI API キー
OPENAI_API_KEY=your_api_key
```

### データベースの初期化
1. マイグレーションの実行
```bash
alembic upgrade head
```

2. 初期データの生成（オプション）
```python
from database import DatabaseManager
db = DatabaseManager()
db.generate_sample_data()
```

## 3. アプリケーションの起動

### 開発環境での起動
```bash
streamlit run main.py
```

### Replit での実行
1. `.replit` ファイルが正しく設定されていることを確認
2. Run ボタンをクリック

## 4. 設定とカスタマイズ

### AI モデル設定
- 設定ページから AI モデルのパラメータを調整可能
- モデル選択: GPT-4 または GPT-3.5-turbo
- Temperature と max_tokens の調整

### キャッシュ設定
- キャッシュの有効/無効
- TTL（Time To Live）の設定
- 最大キャッシュサイズの設定

### 評価指標のカスタマイズ
- メトリクスページから新しい評価指標を追加可能
- 重み付けの調整
- カテゴリーの選択（core/custom）

## 5. トラブルシューティング

### 一般的な問題と解決方法
1. データベース接続エラー
   - DATABASE_URL の確認
   - PostgreSQL サーバーの稼働確認

2. OpenAI API エラー
   - API キーの有効性確認
   - 利用制限の確認

3. パフォーマンスの問題
   - キャッシュ設定の最適化
   - データベースインデックスの確認

### ログの確認方法
- アプリケーションログの場所
- エラーログの解釈方法
- デバッグモードの有効化

## 6. バックアップとリストア

### データベースのバックアップ
```bash
pg_dump -U username -d dbname > backup.sql
```

### データのリストア
```bash
psql -U username -d dbname < backup.sql
```
