# Created by rupalpatel at 25/03/2022
Feature: Bink BPL - Transaction increases user balance
  As a customer
  I am doing transaction and it meets earn threshold
  So I make sure that I got balance increased

  Background:
    Given the trenette retailer exists
    And the retailer's trenette-stmp-campaign-1 STAMPS campaign starts 5 days ago and ends in a day and is ACTIVE
    And the trenette-stmp-campaign-1 campaign has an STAMPS earn rule with a threshold of 500, an increment of 100 and a multiplier of 1
    And the trenette-stmp-campaign-1 campaign has reward rule of 700, with reward slug free-item and allocation window 0
    And required fetch type are configured for the current retailer
    And that campaign has the standard reward config configured with 1 allocable rewards

  @bpl @transaction @bpl-294
  Scenario: Transaction meets earn threshold (>0)
    Given an active account holder exists for the retailer
    When BPL receives a transaction for the account holder for the amount of 550 pennies
    Then 0 rewards are available to the account holder
    When BPL receives a transaction for the account holder for the amount of 550 pennies
    Then 0 rewards are available to the account holder
    And the account holder's trenette-stmp-campaign-1 balance is 200
    When BPL receives a transaction for the account holder for the amount of 600 pennies
    Then 0 rewards are available to the account holder
    And the account holder's trenette-stmp-campaign-1 balance is 300
