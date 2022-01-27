from sqlalchemy.ext.automap import automap_base

from db.carina.session import engine

Base = automap_base()
Base.prepare(engine, reflect=True)

# get models from Base mapping
Rewards = Base.classes.reward
RewardConfig = Base.classes.reward_config
RewardUpdate = Base.classes.reward_update
RewardFileLog = Base.classes.reward_file_log
