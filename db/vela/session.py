from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from settings import VELA_DATABASE_URI

engine = create_engine(VELA_DATABASE_URI, poolclass=NullPool, echo=False)
VelaSessionMaker = sessionmaker(bind=engine)
