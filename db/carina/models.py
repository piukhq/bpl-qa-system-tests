from sqlalchemy.ext.automap import automap_base

from db.carina.session import engine

Base = automap_base()
Base.prepare(engine, reflect=True)

# get models from Base mapping
Voucher = Base.classes.voucher
VoucherConfig = Base.classes.voucher_config
VoucherAllocation = Base.classes.voucher_allocation
