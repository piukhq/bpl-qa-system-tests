Feature: Bink BPL - Activate new campaign, end old with balances and rewards STAMPS
    As a retailer
    I want to activate a new campaign and end an old one, so I make sure
    new zero balances are created and any old rewards or balances are deleted

    Background:
        Given the trenette retailer exists
        And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None
        And the retailer's trenette-active-campaign STAMPS campaign starts 10 days ago and ends in a day and is ACTIVE
        And the trenette-active-campaign campaign has an earn rule with a threshold of 500, an increment of 100, a multiplier of 1 and max amount of 0
        And the trenette-active-campaign campaign has reward rule with reward goal: 700, reward slug: 10percentoff, allocation window: 0 and reward cap: 0
        And the retailer has a 10percentoff reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type

        And the retailer's trenette-draft-campaign STAMPS campaign starts 5 days ago and ends in a week and is DRAFT
        And the trenette-draft-campaign campaign has an earn rule with a threshold of 1000, an increment of 200, a multiplier of 1 and max amount of 0
        And the trenette-draft-campaign campaign has reward rule with reward goal: 900, reward slug: free-item, allocation window: 0 and reward cap: 0
        And the retailer has a free-item reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type


    @bpl @campaign @bpl-290
    Scenario: Activate new campaign, cancel old - stamp campaign
        Given an active account holder exists for the retailer
        And the account holder's trenette-active-campaign balance is 500
        And there are 3 issued unexpired rewards for account holder with reward slug 10percentoff and campaign slug trenette-active-campaign

        When the retailer's trenette-draft-campaign campaign status is changed to active

        And BPL receives a transaction for the account holder for the amount of 600 pennies
        And the task worker queue is full
        And the retailer's trenette-active-campaign campaign status is changed to cancelled
        And the task worker queue is ready

        Then the account holder's trenette-active-campaign balance does not exist
        And the vela reward-adjustment task status is cancelled

        And the account holder balance shown for trenette-draft-campaign is 0
        And any trenette account holder rewards for 10percentoff are cancelled


    @bpl @campaign @bpl-512
    Scenario: Activate new campaign, cancel old with no allocated rewards - stamp campaign
        Given an active account holder exists for the retailer
        And the retailer's trenette-draft-campaign campaign status is changed to active
        And the retailer's trenette-active-campaign campaign status is changed to cancelled

        Then the carina cancel-rewards task status is success