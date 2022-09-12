# Created by rupalpatel at 06/04/2022
Feature: Transaction with no reward config setup for retailer
  As a customer
  There is no reward configured
  So I make sure that balance get increase whatever I transact

  Background:
    Given the trenette retailer exists
    And the retailer's trenette-acc-campaign-1 ACCUMULATOR campaign starts 5 days ago and ends in a day and is ACTIVE
    And the trenette-acc-campaign-1 campaign has an earn rule with a threshold of 10, an increment of 0, a multiplier of 1 and max amount of 0
    And the trenette-acc-campaign-1 campaign has reward rule of 10000, with reward slug 10percentoff and allocation window 0
    And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None
    And the retailer has a 10percentoff reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type

  @bpl @transaction @bpl-297
  Scenario: single rewards become available after the transaction is processed [No rewards available prior to transaction arriving]
    Given an active account holder exists for the retailer
    When BPL receives a transaction for the account holder for the amount of 7500 pennies
    Then the account holder's trenette-acc-campaign-1 balance is returned as 7500
    And 0 issued rewards are available to the account holder
    When BPL receives a transaction for the account holder for the amount of 5050 pennies
    Then the account holder's trenette-acc-campaign-1 balance is returned as 2550
    And 0 issued rewards are available to the account holder
    When 1 rewards are generated for the 10percentoff reward config with allocation status set to false and deleted status set to false
    Then rewards are allocated to the account holder for the 10percentoff reward
    And the account holder's trenette-acc-campaign-1 balance is returned as 2550
    And 1 issued rewards are available to the account holder


  @bpl @transaction @bpl-297
  Scenario: Two rewards become available after the transaction is processed [No rewards available prior to transaction arriving]
    Given an active account holder exists for the retailer
    When BPL receives a transaction for the account holder for the amount of 21000 pennies
    Then the account holder's trenette-acc-campaign-1 balance is returned as 1000
    And 0 issued rewards are available to the account holder
    When 2 rewards are generated for the 10percentoff reward config with allocation status set to false and deleted status set to false
    Then rewards are allocated to the account holder for the 10percentoff reward
    And the account holder's trenette-acc-campaign-1 balance is returned as 1000
    And 2 issued rewards are available to the account holder