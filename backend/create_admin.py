import sys
import uuid
from datetime import datetime
from getpass import getpass

from app.api.endpoints.auth import get_password_hash
from app.db.models import User, get_db_context, init_db


def create_admin_user(username, email, password):
    """管理者ユーザーを作成する"""
    try:
        # データベースの初期化
        init_db()

        with get_db_context() as db:
            # 既存のユーザーをチェック
            if db.query(User).filter(User.username == username).first():
                print(f"ユーザー名 '{username}' は既に使用されています")
                return False

            if db.query(User).filter(User.email == email).first():
                print(f"メールアドレス '{email}' は既に使用されています")
                return False

            # パスワードをハッシュ化
            hashed_password = get_password_hash(password)

            # 新しい管理者ユーザーを作成
            # 明示的に ID を生成
            user_id = str(uuid.uuid4())

            admin_user = User(
                id=user_id,  # 明示的に ID を設定
                username=username,
                email=email,
                hashed_password=hashed_password,
                is_active=True,
                is_admin=True,
                created_at=datetime.utcnow().isoformat(),
            )

            db.add(admin_user)
            db.commit()

            print(f"管理者ユーザー '{username}' が作成されました")
            return True

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("管理者ユーザーの作成")
    print("-----------------")

    if len(sys.argv) > 1:
        username = sys.argv[1]
    else:
        username = input("ユーザー名: ")

    if len(sys.argv) > 2:
        email = sys.argv[2]
    else:
        email = input("メールアドレス: ")

    if len(sys.argv) > 3:
        password = sys.argv[3]
    else:
        password = getpass("パスワード: ")
        confirm_password = getpass("パスワード（確認）: ")
        if password != confirm_password:
            print("パスワードが一致しません")
            sys.exit(1)

    success = create_admin_user(username, email, password)

    if not success:
        sys.exit(1)
