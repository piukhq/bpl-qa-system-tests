# Created by Rupal Patel at 06/10/2022
Feature: Bink BPL - Decoupling reward type
    As a customer
    I want to make sure that when there are multiple campaigns
    then i can use same reward slug for all campaign

    Background:
        Given the trenette retailer exists
        And the retailer has a REWARD_ISSUANCE email template configured with template id 99999999
        And the email template with template id 99999999 has the following required template variables: reward_url, account_number, first_name

        And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None

        And the retailer has a 10percentoff reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type
        And there is 5 rewards configured for the 10percentoff reward config, with allocation status set to false and deleted status set to false

# Add assertion once the epic is in shape
    @bpl @campaign-accumulator @bpl-724
    Scenario: Single reward slug can be used against multiple campaign - accumulator

        Given the retailer's trenette-active-campaign ACCUMULATOR campaign starts 10 days ago and ends in a day and is ACTIVE
        And the trenette-active-campaign campaign has an earn rule with a threshold of 500, an increment of None, a multiplier of 1 and max amount of 0
        And the trenette-active-campaign campaign has reward rule with reward goal: 700, reward slug: 10percentoff, allocation window: 30 and reward cap: 3
        And the retailer's trenette-active-campaign campaign with reward_slug: 10percentoff added as ACTIVE

        And the retailer's trenette-draft-campaign ACCUMULATOR campaign starts 5 days ago and ends in a week and is DRAFT
        And the trenette-draft-campaign campaign has an earn rule with a threshold of 1000, an increment of None, a multiplier of 1 and max amount of 0
        And the trenette-draft-campaign campaign has reward rule with reward goal: 900, reward slug: 10percentoff, allocation window: 30 and reward cap: 0
        And the retailer's trenette-draft-campaign campaign with reward_slug: 10percentoff added as DRAFT

        When the retailer's trenette-draft-campaign campaign status is changed to active
        And the retailer's trenette-active-campaign campaign status is changed to cancelled

        Given the retailer's trenette-draft-campaign_new ACCUMULATOR campaign starts 5 days ago and ends in a week and is DRAFT
        And the trenette-draft-campaign_new campaign has an earn rule with a threshold of 2000, an increment of None, a multiplier of 2 and max amount of 0
        And the trenette-draft-campaign_new campaign has reward rule with reward goal: 900, reward slug: 10percentoff, allocation window: 30 and reward cap: 1

        When the retailer's trenette-draft-campaign_new campaign status is changed to active
        And the retailer's trenette-draft-campaign campaign status is changed to ended

    @bpl @campaign-stamps @bpl-724
    Scenario: Single reward slug can be used against multiple campaign - stamps

        Given the retailer's trenette-active-campaign STAMPS campaign starts 10 days ago and ends in a day and is ACTIVE
        And the trenette-active-campaign campaign has an earn rule with a threshold of 500, an increment of 100, a multiplier of 1 and max amount of 0
        And the trenette-active-campaign campaign has reward rule with reward goal: 1000, reward slug: 10percentoff, allocation window: 0 and reward cap: 0
        And the retailer's trenette-active-campaign campaign with reward_slug: 10percentoff added as ACTIVE

        And the retailer's trenette-draft-campaign STAMPS campaign starts 2 days ago and ends in a week and is DRAFT
        And the trenette-draft-campaign campaign has an earn rule with a threshold of 1000, an increment of 200, a multiplier of 1 and max amount of 0
        And the trenette-draft-campaign campaign has reward rule with reward goal: 900, reward slug: 10percentoff, allocation window: 0 and reward cap: 0
        And the retailer's trenette-draft-campaign campaign with reward_slug: 10percentoff added as DRAFT

        When the retailer's trenette-draft-campaign campaign status is changed to active
        And the retailer's trenette-active-campaign campaign status is changed to cancelled

        Given the retailer's trenette-draft-campaign_new STAMPS campaign starts 5 days ago and ends in a week and is DRAFT
        And the trenette-draft-campaign_new campaign has an earn rule with a threshold of 2000, an increment of 200, a multiplier of 2 and max amount of 0
        And the trenette-draft-campaign_new campaign has reward rule with reward goal: 900, reward slug: 10percentoff, allocation window: 0 and reward cap: 0

        When the retailer's trenette-draft-campaign_new campaign status is changed to active
        And the retailer's trenette-draft-campaign campaign status is changed to ended

