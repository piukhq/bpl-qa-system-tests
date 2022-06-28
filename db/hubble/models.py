from sqlalchemy.ext.automap import AutomapBase, automap_base

Base: AutomapBase = automap_base()


class Activity(Base):
    __tablename__ = "activity"
