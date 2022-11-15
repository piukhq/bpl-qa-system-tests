Feature: Bink BPL - refund (max amount set)
    As a customer
    I want to transact some negative amount
    So I make sure that balance and pending window should updated

    Background:
        Given the trenette retailer exists with status as TEST
        And the retailer's trenette-accumulator ACCUMULATOR campaign starts 5 days ago and ends in a day and is ACTIVE
        And the trenette-accumulator campaign has an earn rule with a threshold of 200, an increment of None, a multiplier of 1 and max amount of 500
        And the trenette-accumulator campaign has reward rule with reward goal: 1000, reward slug: free-item, allocation window: 1 and reward cap: 0
        And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None
        And the retailer has a free-item reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type
        And the retailer's trenette-accumulator campaign with reward_slug: free-item added as ACTIVE
        And there is 0 rewards configured for the free-item reward config, with allocation status set to false and deleted status set to false

    @bpl @transaction @refund @bpl-670
    Scenario: Refund accepted above max amount
        Given an active account holder exists for the retailer
        When BPL receives a transaction for the account holder for the amount of 2000 pennies
        Then BPL responds with a HTTP 200 and awarded message
        And the account holder balance shown for trenette-accumulator is 500
        When BPL receives a transaction for the account holder for the amount of 2000 pennies
        Then BPL responds with a HTTP 200 and awarded message
        And 1 pending rewards are available to the account holder for the trenette-accumulator campaign
        And the account holder balance shown for trenette-accumulator is 0
        When BPL receives a transaction for the account holder for the amount of -700 pennies
        Then BPL responds with a HTTP 200 and refund_accepted message
        And 0 pending rewards are available to the account holder for the trenette-accumulator campaign
        And the account holder balance shown for trenette-accumulator is 500
        When BPL receives a transaction for the account holder for the amount of -300 pennies
        Then BPL responds with a HTTP 200 and refund_accepted message
        And the account holder balance shown for trenette-accumulator is 200
        And 0 pending rewards are available to the account holder for the trenette-accumulator campaign
