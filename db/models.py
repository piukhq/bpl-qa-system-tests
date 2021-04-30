from sqlalchemy.ext.automap import automap_base

from db.session import engine

Base = automap_base()
Base.prepare(engine, reflect=True)

# get models from Base mapping
AccountHolder = Base.classes.account_holder
AccountHolderProfile = Base.classes.account_holder_profile
EnrolmentCallback = Base.classes.enrolment_callback
Retailer = Base.classes.retailer
