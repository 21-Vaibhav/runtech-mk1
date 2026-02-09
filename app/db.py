from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


engine = create_engine(f"sqlite:///{settings.sqlite_path}", echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    from app.storage.repository import (
        Activity,
        ActivityStream,
        DailyRecommendation,
        FeedbackEvent,
        ModelStateSnapshot,
    )

    Base.metadata.create_all(bind=engine)
