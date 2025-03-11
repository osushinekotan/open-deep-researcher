import sqlite3

from app.config import DATA_DIR

DB_DIR = DATA_DIR / "db"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "application.db"


class Database:
    """SQLiteデータベース管理の基本クラス"""

    def __init__(self, db_path=DB_PATH):
        """初期化とデータベース接続の準備"""
        self.db_path = db_path
        self._setup_database()

    def _setup_database(self):
        """データベースの初期セットアップ"""
        # データベースファイルが存在しない場合は作成される
        conn = self._get_connection()
        conn.close()

    def _get_connection(self):
        """データベース接続を取得"""
        conn = sqlite3.connect(str(self.db_path))
        # 辞書形式で結果を取得できるように設定
        conn.row_factory = sqlite3.Row
        return conn

    def execute_query(self, query: str, params: tuple = ()):
        """SQLクエリを実行"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor
        finally:
            conn.close()

    def fetch_all(self, query: str, params: tuple = ()):
        """SELECT クエリを実行して全ての結果を取得"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def fetch_one(self, query: str, params: tuple = ()):
        """SELECT クエリを実行して1つの結果を取得"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def create_tables(self):
        """必要なテーブルを作成する（サブクラスでオーバーライド）"""
        pass


# グローバルインスタンス
_database = None


def get_database() -> Database:
    """データベースのシングルトンインスタンスを取得"""
    global _database
    if _database is None:
        _database = Database()
    return _database
