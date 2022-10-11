# Created by Haffi Mazhar at 21/04/2022
Feature: Bink BPL - Trigger transaction and cancel campaign while balance adjustments pending
    As a customer
    I want to make sure that when an active campaign is cancelled
    that any old unallocated rewards and campaign balances are deleted and
    that any account holder rewards are cancelled and
    that any pending tasks which were triggered by transaction request are cancelled

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




    @bpl @campaign @transaction @bpl-295
    Scenario: Trigger transaction and cancel campaign
        Given an active account holder exists for the retailer
        And the account holder's trenette-active-campaign balance is 500
        And there are 3 issued unexpired rewards for account holder with reward slug 10percentoff and campaign slug campaign_slug

        When the retailer's trenette-draft-campaign campaign status is changed to active
        And BPL receives a transaction for the account holder for the amount of 600 pennies
        And the task worker queue is full
        And the retailer's trenette-active-campaign campaign status is changed to cancelled
        And the task worker queue is ready

        Then all unallocated rewards for 10percentoff reward config are soft deleted
        And the vela reward-adjustment task status is cancelled
        And the account holder's trenette-active-campaign balance does not exist
        And the account holder balance shown for trenette-draft-campaign is 0
        And 3 cancelled rewards are available to the account holder for the trenette-active-campaign campaign
        And there is no balance shown for trenette-active-campaign for account holder
