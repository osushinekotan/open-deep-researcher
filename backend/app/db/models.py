from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from app.config import DATA_DIR

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATA_DIR}/application.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Research(Base):
    """リサーチ情報のテーブル"""

    __tablename__ = "research"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.username", ondelete="CASCADE"))
    topic = Column(String, nullable=False)
    status = Column(String, nullable=False)
    config = Column(Text)  # JSON形式で保存
    created_at = Column(String, nullable=False)
    completed_at = Column(String)
    updated_at = Column(String, nullable=False)
    progress = Column(Float, default=0.0)
    error = Column(Text)
    waiting_for_feedback = Column(Boolean, default=False)
    introduction = Column(Text)
    conclusion = Column(Text)
    final_report = Column(Text)

    # リレーションシップ
    sections = relationship("Section", back_populates="research", cascade="all, delete-orphan")
    urls = relationship("URL", back_populates="research", cascade="all, delete-orphan")


class Section(Base):
    """セクション情報のテーブル"""

    __tablename__ = "sections"

    id = Column(Integer, primary_key=True, index=True)
    research_id = Column(String, ForeignKey("research.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    content = Column(Text)
    search_options = Column(Text)  # JSON形式で保存
    is_completed = Column(Boolean, default=False)

    research = relationship("Research", back_populates="sections")


class URL(Base):
    """URLのテーブル"""

    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, index=True)
    research_id = Column(String, ForeignKey("research.id", ondelete="CASCADE"), nullable=False)
    url = Column(String, nullable=False)

    research = relationship("Research", back_populates="urls")


class User(Base):
    """ユーザー情報のテーブル"""

    __tablename__ = "users"

    username = Column(String, primary_key=True, index=True)
    created_at = Column(String, nullable=False)

    # リレーションシップ
    researches = relationship("Research", backref="user")


def init_db():
    Base.metadata.create_all(bind=engine)


# データベースセッションを取得する関数
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_context():
    db = SessionLocal()
    try:
        return db
    except:
        db.close()
        raise
