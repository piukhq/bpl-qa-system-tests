from sqlalchemy.ext.automap import automap_base
from retry_tasks_lib.db.models import load_models_to_metadata
from db.carina.session import engine

Base = automap_base()
Base.prepare(engine, reflect=True)
load_models_to_metadata(Base.metadata)

# get models from Base mapping
Voucher = Base.classes.voucher
VoucherConfig = Base.classes.voucher_config
VoucherUpdate = Base.classes.voucher_update
