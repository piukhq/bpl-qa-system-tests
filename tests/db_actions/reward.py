# @pytest.fixture(scope="function")
# def get_reward_config(carina_db_session: "Session") -> Callable:
#     def func(retailer_id: int, reward_slug: Optional[str] = None) -> RewardConfig:
#         query = select(RewardConfig).where(RewardConfig.retailer_id == retailer_id)
#         if reward_slug is not None:
#             query = query.where(RewardConfig.reward_slug == reward_slug)
#         return carina_db_session.execute(query).scalars().first()
#
#     return func
