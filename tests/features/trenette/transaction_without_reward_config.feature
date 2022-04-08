# Created by rupalpatel at 06/04/2022
Feature: Transaction with no reward config setup for retailer
  As a customer
  There is no reward configured
  So I make sure that balance get increase whatever I transact

  Background:
    Given the trenette retailer exists
    And the retailer's trenette-acc-campaign-1 ACCUMULATOR campaign starts 5 days ago and ends in a day and is ACTIVE
    And the trenette-acc-campaign-1 campaign has an ACCUMULATOR earn rule with a threshold of 10, an increment of 0 and a multiplier of 1
    And the trenette-acc-campaign-1 campaign has reward rule of 10000, with reward slug 10percentoff and allocation window 0
    And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None
    And the retailer has a 10percentoff reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type

  @transaction @bpl @bpl-297
  Scenario: Transaction without rewards configured - 1 reward setup
    Given an active account holder exists for the retailer
    When BPL receives a transaction for the account holder for the amount of 7500 pennies
    Then the account holder's trenette-acc-campaign-1 accumulator campaign balance 7500 is updated
    And 0 rewards are available to the account holder
    When BPL receives a transaction for the account holder for the amount of 5050 pennies
    Then the account holder's trenette-acc-campaign-1 accumulator campaign balance 2550 is updated
    And 0 rewards are available to the account holder
    When 1 reward configured for the 10percentoff reward config, with allocation status set to false and deleted status set to false
    Then a Reward code will be allocated asynchronously for 10percentoff reward
    And the account holder's trenette-acc-campaign-1 accumulator campaign balance 2550 is updated
    And 1 rewards are available to the account holder


  @transaction @bpl @bpl-297
  Scenario: Transaction without rewards configured - 2 reward setup
    Given an active account holder exists for the retailer
    When BPL receives a transaction for the account holder for the amount of 21000 pennies
    Then the account holder's trenette-acc-campaign-1 accumulator campaign balance 1000 is updated
    And 0 rewards are available to the account holder
    When 2 reward configured for the 10percentoff reward config, with allocation status set to false and deleted status set to false
    Then a Reward code will be allocated asynchronously for 10percentoff reward
    And the account holder's trenette-acc-campaign-1 accumulator campaign balance 1000 is updated
    And 2 rewards are available to the account holder
