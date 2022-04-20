# Created by Haffi Mazhar at 29/03/2022
Feature: Bink BPL - Activate new campaign, end old
    As a customer
    I want to transact some amount
    So I make sure that balance get increase and reward goal meet

    Background:
        Given the trenette retailer exists
        And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None

        And the retailer's trenette-active-campaign STAMPS campaign starts 10 days ago and ends in a day and is ACTIVE
        And the trenette-active-campaign campaign has an STAMPS earn rule with a threshold of 500, an increment of 100 and a multiplier of 1
        And the trenette-active-campaign campaign has reward rule of 700, with reward slug 10percentoff and allocation window 0
        And the retailer has a 10percentoff reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type
        And there is 5 reward configured for the 10percentoff reward config, with allocation status set to false and deleted status set to false

        And the retailer's trenette-draft-campaign STAMPS campaign starts 5 days ago and ends in a week and is DRAFT
        And the trenette-draft-campaign campaign has an STAMPS earn rule with a threshold of 1000, an increment of 200 and a multiplier of 1
        And the trenette-draft-campaign campaign has reward rule of 900, with reward slug free-item and allocation window 0
        And the retailer has a free-item reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type
        And there is 5 reward configured for the free-item reward config, with allocation status set to false and deleted status set to false


    @bpl @campaign @bpl-289
    Scenario Outline: Active campaign is ended and draft campaign is activated
        Given an active account holder exists for the retailer
        And the trenette-active-campaign account holder campaign balance is 500
        And the account has 3 pending rewards for trenette-active-campaign with value 700
        And the account has 3 issued unexpired rewards

        Then the status is then changed to active for trenette-draft-campaign for the retailer trenette
        When BPL receives a transaction for the account holder for the amount of 600 pennies
        And the task worker queue is full
        Then the status is then changed to ended for trenette-active-campaign for the retailer trenette
        When the task worker queue is ready
        And the reward-adjustment task status is cancelled

        Then all unallocated rewards for 10percentoff reward config are soft deleted
        And the account holder's trenette-active-campaign balance no longer exists
        And the account holder's trenette-draft-campaign balance is 0
        And 3 rewards are available to the account holder
