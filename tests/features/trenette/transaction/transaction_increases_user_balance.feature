# Created by rupalpatel at 25/03/2022
Feature: Bink BPL - Transaction increases user balance
  As a customer
  I am doing transaction and it meets earn threshold
  So I make sure that I got balance increased

  Background:
    Given the trenette retailer exists
    And the retailer's trenette-stmp-campaign-1 STAMPS campaign starts 5 days ago and ends in a day and is ACTIVE
    And the trenette-stmp-campaign-1 campaign has an earn rule with a threshold of 500, an increment of 100, a multiplier of 1 and max amount of 0
    And the trenette-stmp-campaign-1 campaign has reward rule with reward goal: 700, reward slug: free-item, allocation window: 0 and reward cap: 0
    And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None
    And the retailer has a free-item reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type
    And the retailer's trenette-stmp-campaign-1 campaign with reward_slug: free-item added as ACTIVE
    And there is 1 rewards configured for the free-item reward config, with allocation status set to false and deleted status set to false

  @bpl @transaction @bpl-294
  Scenario: Transaction meets earn threshold (>0)
    Given an active account holder exists for the retailer
    When BPL receives a transaction for the account holder for the amount of 550 pennies
    Then 0 issued rewards are available to the account holder for the trenette-stmp-campaign-1 campaign
    When BPL receives a transaction for the account holder for the amount of 550 pennies
    Then 0 issued rewards are available to the account holder for the trenette-stmp-campaign-1 campaign
    And the account holder balance shown for trenette-stmp-campaign-1 is 200
    When BPL receives a transaction for the account holder for the amount of 600 pennies
    Then 0 issued rewards are available to the account holder for the trenette-stmp-campaign-1 campaign
    And the account holder balance shown for trenette-stmp-campaign-1 is 300
