# Created by rupalpatel at 23/05/2022
Feature: Bink BPL - Transaction increases user balance for accumulator campaign, reward goal met
  As a customer
  I want to transact some amount
  So I make sure that balance get increase and reward goal meet

  Background:
    Given the trenette retailer exists
    And the retailer's trenette-accumulator ACCUMULATOR campaign starts 5 days ago and ends in a day and is ACTIVE
    And the trenette-accumulator campaign has an ACCUMULATOR earn rule with a threshold of 200, an increment of 100 and a multiplier of 1
    And the trenette-accumulator campaign has reward rule of 700, with reward slug free-item and allocation window 0
    And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None
    And the retailer has a free-item reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type
    And there is 1 reward configured for the free-item reward config, with allocation status set to false and deleted status set to false

  @transaction @bpl @test
  Scenario: Account holder is rewarded when reward threshold is met - Accumulator
    Given an active account holder exists for the retailer
    When BPL receives a transaction for the account holder for the amount of 100 pennies
    Then the account holder's transaction Threshold not met
    And the account holder's trenette-accumulator balance is 0
    And 0 issued rewards are available to the account holder
    When BPL receives a transaction for the account holder for the amount of 500 pennies
    Then the account holder's transaction Awarded
    And the account holder's trenette-accumulator balance is 500
    And 0 issued rewards are available to the account holder
    When BPL receives a transaction for the account holder for the amount of 300 pennies
    Then the account holder's transaction Awarded
    And the account holder's trenette-accumulator balance is 100
    And 1 issued rewards are available to the account holder
