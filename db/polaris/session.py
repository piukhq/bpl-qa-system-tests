from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from settings import POLARIS_DATABASE_URI

engine = create_engine(POLARIS_DATABASE_URI, poolclass=NullPool, echo=False)
PolarisSessionMaker = sessionmaker(bind=engine)
