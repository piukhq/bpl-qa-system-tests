# Created by Haffi Mazhar 26/08/2022
Feature: Bink BPL - Transaction with a reward cap with no allocation window
    As a customer
    I want to transact some amount
    Where a campaign reward rule has transaction reward cap (TRC) set and no allocation window
    So I make sure that rewards issuance are done correctly adhering to TRC

    Background:
        Given the trenette retailer exists with status as TEST
        And the retailer has a REWARD_ISSUANCE email template configured with template id 99999999
        And the email template with template id 99999999 has the following required template variables: reward_url, account_number, first_name
        And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None
        And the retailer has a free-item reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type

        And the retailer's trenette-acc-campaign ACCUMULATOR campaign starts 5 days ago and ends in a day and is ACTIVE
        And the trenette-acc-campaign campaign has an earn rule with a threshold of 0, an increment of 0, a multiplier of 1 and max amount of 0
        And the trenette-acc-campaign campaign has reward rule with reward goal: 10000, allocation window: 0 and reward cap: 2
        And 5 unassigned rewards are generated for the free-item reward config with deleted status set to false

    @bpl @trc @bpl-702
    Scenario Outline: Transaction with reward cap
        Given an active account holder exists for the retailer
        And the account holder's trenette-acc-campaign balance is <starting_balance>
        When BPL receives a transaction for the account holder for the amount of <tx_amount> pennies
        Then the account holder balance shown for trenette-acc-campaign is <final_balance>
        And <issued_rewards_amount> issued rewards are available to the account holder for the trenette-acc-campaign campaign

        Examples:
            | starting_balance | tx_amount | final_balance | issued_rewards_amount |
            | 0                | 55000     | 0             | 2                     |
            | 7500             | 25000     | 7500          | 2                     |
            | 7500             | 2900      | 400           | 1                     |
