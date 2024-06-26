# Created by Haffi Mazhar at 29/03/2022
Feature: Bink BPL - Activate new campaign, end old
    As a customer
    I want to make sure that when an active campaign is ended
    that any old unallocated rewards and campaign balances are deleted and
    that any pending tasks are cancelled

    Background:
        Given the trenette retailer exists with status as TEST
        And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None

        And the retailer's trenette-active-campaign STAMPS campaign starts 10 days ago and ends in a day and is ACTIVE
        And the trenette-active-campaign campaign has an earn rule with a threshold of 500, an increment of 100, a multiplier of 1 and max amount of 0
        And the trenette-active-campaign campaign has reward rule with reward goal: 700, reward slug: 10percentoff, allocation window: 0 and reward cap: 0
        And the retailer has a 10percentoff reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type
        And the retailer's trenette-active-campaign campaign with reward_slug: 10percentoff added as ACTIVE
        And there is 5 rewards configured for the 10percentoff reward config, with allocation status set to false and deleted status set to false

        And the retailer's trenette-draft-campaign STAMPS campaign starts 5 days ago and ends in a week and is DRAFT
        And the trenette-draft-campaign campaign has an earn rule with a threshold of 1000, an increment of 200, a multiplier of 1 and max amount of 0
        And the trenette-draft-campaign campaign has reward rule with reward goal: 900, reward slug: free-item, allocation window: 0 and reward cap: 0
        And the retailer has a free-item reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type
        And the retailer's trenette-draft-campaign campaign with reward_slug: free-item added as DRAFT
        And there is 5 rewards configured for the free-item reward config, with allocation status set to false and deleted status set to false


    @bpl @campaign @bpl-289
    Scenario: Active campaign is ended and draft campaign is activated
        Given an active account holder exists for the retailer
        And the account holder's trenette-active-campaign balance is 500
        And the account has 3 pending rewards for the trenette-active-campaign campaign and 10percentoff reward slug with value 700
        And the account has 3 issued unexpired rewards for the trenette-active-campaign campaign

        And the retailer's trenette-draft-campaign campaign status is changed to active
        And BPL receives a transaction for the account holder for the amount of 600 pennies
        And the task worker queue is full
        And the retailer's trenette-active-campaign campaign status is changed to ended
        When the task worker queue is ready

        Then all unallocated rewards for 10percentoff reward config are not soft deleted
        And the vela reward-adjustment task status is cancelled
        And the account holder's trenette-active-campaign balance does not exist
        And the account holder balance shown for trenette-draft-campaign is 0
        And 3 issued rewards are available to the account holder for the trenette-active-campaign campaign
