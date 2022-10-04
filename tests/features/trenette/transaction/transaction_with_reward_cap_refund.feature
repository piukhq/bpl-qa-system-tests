# Created by rupalpatel at 23/09/2022
Feature: Bink BPL - Transaction with a reward cap and refund window
    As a customer
    I want to transact some amount
    Where a campaign reward rule has transaction reward cap (TRC) set with refund window
    So I make sure that rewards issuance are done correctly adhering to TRC

    Background:
        Given the trenette retailer exists
        And the retailer's trenette-acc-campaign ACCUMULATOR campaign starts 5 days ago and ends in a day and is ACTIVE
        And the trenette-acc-campaign campaign has an earn rule with a threshold of 0, an increment of None, a multiplier of 1 and max amount of 0
        And the trenette-acc-campaign campaign has reward rule with reward goal: 20000, reward slug: 10percentoff, allocation window: 10 and reward cap: 2
        And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None
        And the retailer has a 10percentoff reward config configured with validity_days: 10, and a status of ACTIVE and a PRE_LOADED fetch type
        And there is 5 rewards configured for the 10percentoff reward config, with allocation status set to false and deleted status set to false

    @bpl @trc @AC-1-2 @bpl-733
    Scenario: verify Purchase > TRC - Pending reward issued, no balance change
        Given an active account holder exists for the retailer
        And the account holder's trenette-acc-campaign balance is 2000
        When BPL receives a transaction for the account holder for the amount of 65000 pennies
        Then 2 pending rewards are available to the account holder
        And the account holder balance shown for trenette-acc-campaign is 2000

    @bpl @trc @AC-3 @bpl-733
    Scenario: verify there is slush available on one pending reward
        Given an active account holder exists for the retailer
        And the account holder's trenette-acc-campaign balance is 2000

        When the account has a pending rewards with count of 2, value 10000, total cost to user 50000 for trenette-acc-campaign campaign and 10percentoff reward slug with a conversion date in 10 days
        And the account has a pending rewards with count of 2, value 10000, total cost to user 24500 for trenette-acc-campaign campaign and 10percentoff reward slug with a conversion date in 10 days

        When BPL receives a transaction for the account holder for the amount of -5000 pennies
        Then BPL responds with a HTTP 200 and refund_accepted message

        And the account holder balance shown for trenette-acc-campaign is 2000
        And the account holder has 2 pending reward records for the trenette-acc-campaign campaign
        And the account holder's 1st pending reward record for trenette-acc-campaign has count of 2, value of 10000 and total cost to user of 45000 with a conversion date in 10 days
        And the account holder's 2nd pending reward record for trenette-acc-campaign has count of 2, value of 10000 and total cost to user of 24500 with a conversion date in 10 days

    @bpl @trc @AC-4 @bpl-733
    Scenario: verify there is slush available over multiple pending reward
        Given an active account holder exists for the retailer
        And the account holder's trenette-acc-campaign balance is 2000

        When the account has a pending rewards with count of 3, value 10000, total cost to user 31000 for trenette-acc-campaign campaign and 10percentoff reward slug with a conversion date in 10 days
        And the account has a pending rewards with count of 2, value 10000, total cost to user 21000 for trenette-acc-campaign campaign and 10percentoff reward slug with a conversion date in 10 days

        When BPL receives a transaction for the account holder for the amount of -1500 pennies
        Then BPL responds with a HTTP 200 and refund_accepted message

        And the account holder balance shown for trenette-acc-campaign is 2000
        And the account holder has 2 pending reward records for the trenette-acc-campaign campaign
        And the account holder's 1st pending reward record for trenette-acc-campaign has count of 3, value of 10000 and total cost to user of 30500 with a conversion date in 10 days
        And the account holder's 2nd pending reward record for trenette-acc-campaign has count of 2, value of 10000 and total cost to user of 20000 with a conversion date in 10 days

    @bpl @trc @AC-5 @bpl-733
    Scenario: verify when a refund happens and there is not enough slush, balance gets affected
        Given an active account holder exists for the retailer
        And the account holder's trenette-acc-campaign balance is 500

        When the account has a pending rewards with count of 3, value 10000, total cost to user 31000 for trenette-acc-campaign campaign and 10percentoff reward slug with a conversion date in 10 days
        And the account has a pending rewards with count of 2, value 10000, total cost to user 21000 for trenette-acc-campaign campaign and 10percentoff reward slug with a conversion date in 10 days

        When BPL receives a transaction for the account holder for the amount of -2500 pennies
        Then BPL responds with a HTTP 200 and refund_accepted message

        And the account holder balance shown for trenette-acc-campaign is 0
        And the account holder has 2 pending reward records for the trenette-acc-campaign campaign
        And the account holder's 1st pending reward record for trenette-acc-campaign has count of 3, value of 10000 and total cost to user of 30000 with a conversion date in 10 days
        And the account holder's 2nd pending reward record for trenette-acc-campaign has count of 2, value of 10000 and total cost to user of 20000 with a conversion date in 10 days

    @bpl @trc @AC-6-733 @bpl-733
    Scenario: verify when a refund happens and there is not enough slush, pending rewards are removed and balance affected
        Given an active account holder exists for the retailer
        And the account holder's trenette-acc-campaign balance is 2000

        When the account has a pending rewards with count of 2, value 10000, total cost to user 27000 for trenette-acc-campaign campaign and 10percentoff reward slug with a conversion date in 10 days
        And the account has a pending rewards with count of 2, value 10000, total cost to user 25000 for trenette-acc-campaign campaign and 10percentoff reward slug with a conversion date in 10 days

        When BPL receives a transaction for the account holder for the amount of -40000 pennies
        Then BPL responds with a HTTP 200 and refund_accepted message

        And the account holder balance shown for trenette-acc-campaign is 4000
        And the account holder's 1st pending reward record for trenette-acc-campaign has count of 1, value of 10000 and total cost to user of 10000 with a conversion date in 10 days


