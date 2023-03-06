Feature: Bink BPL - Decoupling reward type
    As a customer
    I want to make sure that when there are multiple campaigns
    then i can use same reward slug for all campaign

    Background:
        Given the trenette retailer exists with status as TEST
        And the retailer has a REWARD_ISSUANCE email template configured with template id 99999999
        And the email template with template id 99999999 has the following required template variables: reward_url, account_number, first_name

        And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None

        And the retailer has a 10percentoff reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type


    @bpl @campaign-accumulator @bpl-724 @bpl-589 @bpl-2.0
    Scenario: Single reward slug can be used against multiple campaign - accumulator

        Given the retailer's trenette-active-campaign ACCUMULATOR campaign starts 10 days ago and ends in a day and is ACTIVE
        And the trenette-active-campaign campaign has an earn rule with a threshold of 500, an increment of None, a multiplier of 1 and max amount of 0
        And the trenette-active-campaign campaign has reward rule with reward goal: 700, allocation window: 0 and reward cap: 0
        And 5 unassigned rewards are generated for the 10percentoff reward config with deleted status set to false

        And the retailer's trenette-draft-campaign ACCUMULATOR campaign starts 5 days ago and ends in a week and is DRAFT
        And the trenette-draft-campaign campaign has an earn rule with a threshold of 1000, an increment of None, a multiplier of 1 and max amount of 0
        And the trenette-draft-campaign campaign has reward rule with reward goal: 900, allocation window: 0 and reward cap: 0

        And an active account holder exists for the retailer
        When BPL receives a transaction for the account holder for the amount of 1000 pennies
        Then BPL responds with a HTTP 200 and awarded message
        And 1 issued rewards are available to the account holder for the trenette-active-campaign campaign
        And the account holder balance shown for trenette-active-campaign is 300

        When the retailer's trenette-draft-campaign campaign status is changed to active
        And the retailer's trenette-active-campaign campaign status is changed to cancelled
        Then 1 cancelled rewards are available to the account holder for the trenette-active-campaign campaign
        And the status of the allocated account holder for trenette rewards are updated with CANCELLED
        And 1 reward for the account holder shows as cancelled with redeemed date

        Then all unallocated rewards for 10percentoff reward config are not soft deleted

        When BPL receives a transaction for the account holder for the amount of 1000 pennies
        Then BPL responds with a HTTP 200 and awarded message
        And 1 issued rewards are available to the account holder for the trenette-draft-campaign campaign
        And the account holder balance shown for trenette-draft-campaign is 100

    @bpl @campaign-stamps @bpl-724 @bpl-589-1 @bpl-2.0
    Scenario: Single reward slug can be used against multiple campaign - stamps

        Given the retailer's trenette-active-campaign STAMPS campaign starts 10 days ago and ends in a day and is ACTIVE
        And the trenette-active-campaign campaign has an earn rule with a threshold of 500, an increment of 100, a multiplier of 1 and max amount of 0
        And the trenette-active-campaign campaign has reward rule with reward goal: 100, allocation window: 0 and reward cap: 0
        And 5 unassigned rewards are generated for the 10percentoff reward config with deleted status set to false

        And the retailer's trenette-draft-campaign STAMPS campaign starts 2 days ago and ends in a week and is DRAFT
        And the trenette-draft-campaign campaign has an earn rule with a threshold of 100, an increment of 200, a multiplier of 1 and max amount of 0
        And the trenette-draft-campaign campaign has reward rule with reward goal: 100, allocation window: 0 and reward cap: 0

        And an active account holder exists for the retailer
        When BPL receives a transaction for the account holder for the amount of 1000 pennies
        Then BPL responds with a HTTP 200 and awarded message
        And 1 issued rewards are available to the account holder for the trenette-active-campaign campaign
        And the account holder balance shown for trenette-active-campaign is 0

        When the retailer's trenette-draft-campaign campaign status is changed to active
        And the retailer's trenette-active-campaign campaign status is changed to cancelled
        Then 1 cancelled rewards are available to the account holder for the trenette-active-campaign campaign
        And the status of the allocated account holder for trenette rewards are updated with CANCELLED
        And 1 reward for the account holder shows as cancelled with redeemed date

        Then all unallocated rewards for 10percentoff reward config are not soft deleted

        When BPL receives a transaction for the account holder for the amount of 2500 pennies
        Then BPL responds with a HTTP 200 and awarded message
        And 2 issued rewards are available to the account holder for the trenette-draft-campaign campaign
        And the account holder balance shown for trenette-draft-campaign is 0
