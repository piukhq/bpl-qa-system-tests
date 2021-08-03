from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from settings import CARINA_DATABASE_URI

engine = create_engine(CARINA_DATABASE_URI, poolclass=NullPool, echo=False)
CarinaSessionMaker = sessionmaker(bind=engine)
