from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path


def _build_sqlite_url() -> str:
    """Build SQLite URL from env path and ensure parent directory exists."""
    db_path = os.getenv("SQLITE_DB_PATH", "./zyyz_fuping.db")
    sqlite_file = Path(db_path).expanduser()

    if not sqlite_file.is_absolute():
        sqlite_file = (Path.cwd() / sqlite_file).resolve()
    else:
        sqlite_file = sqlite_file.resolve()

    sqlite_file.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{sqlite_file.as_posix()}"

# 根据环境变量选择数据库
# 优先使用 MySQL，如果不可用则使用 SQLite
USE_SQLITE = os.getenv("USE_SQLITE", "false").lower() == "true"

if USE_SQLITE:
    # SQLite 备用配置（用于开发/测试）
    DATABASE_URL = _build_sqlite_url()
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
else:
    # MySQL 数据库连接配置（生产/开发环境）
    mysql_host = os.getenv("MYSQL_HOST", "118.195.146.26")
    mysql_port = int(os.getenv("MYSQL_PORT", "3306"))
    mysql_db = os.getenv("MYSQL_DB", "zyyz_fuping")
    mysql_user = os.getenv("MYSQL_USER", "root")
    mysql_password = os.getenv("MYSQL_PASSWORD", "5130109319@ymxdr")

    DATABASE_URL = URL.create(
        "mysql+pymysql",
        username=mysql_user,
        password=mysql_password,
        host=mysql_host,
        port=mysql_port,
        database=mysql_db,
    )
    
    # 创建引擎，设置连接池和超时
    try:
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            echo=False
        )
        # 尝试连接
        with engine.connect() as conn:
            pass
    except Exception as e:
        # MySQL 连接失败，回退到 SQLite
        print(f"MySQL 连接失败: {str(e)[:100]}")
        print("已自动切换到 SQLite 模式")
        DATABASE_URL = _build_sqlite_url()
        engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False},
            echo=False
        )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
