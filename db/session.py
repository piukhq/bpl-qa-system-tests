from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from settings import SQLALCHEMY_DATABASE_URI

engine = create_engine(SQLALCHEMY_DATABASE_URI, poolclass=NullPool, echo=False)
SessionMaker = sessionmaker(bind=engine)


@contextmanager
def scoped_session() -> Generator:
    session = SessionMaker()
    try:
        yield session
    finally:
        session.close()
