from collections.abc import Generator

from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

settings.db_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    f"sqlite:///{settings.db_path}",
    connect_args={"check_same_thread": False},
)


def init_db() -> None:
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE VIRTUAL TABLE IF NOT EXISTS captured_posts_fts "
                "USING fts5(text, author_name, tokenize='trigram')"
            )
        )


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
