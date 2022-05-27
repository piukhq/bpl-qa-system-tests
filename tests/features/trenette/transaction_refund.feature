# Created by rupalpatel at 23/05/2022
Feature: Bink BPL - refund
  As a customer
  I want to transact some negative amount
  So I make sure that balance and pending window should updated

  Background:
    Given the trenette retailer exists
    And the retailer's trenette-accumulator ACCUMULATOR campaign starts 5 days ago and ends in a day and is ACTIVE
    And the trenette-accumulator campaign has an ACCUMULATOR earn rule with a threshold of 200, an increment of 100 and a multiplier of 1
    And the trenette-accumulator campaign has reward rule of 700, with reward slug free-item and allocation window 1
    And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None
    And the retailer has a free-item reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type
    And there is 1 reward configured for the free-item reward config, with allocation status set to false and deleted status set to false

  @bpl @refund @bpl-540
  Scenario: Refund accepted and balance updated with 0
    Given an active account holder exists for the retailer
    When BPL receives a transaction for the account holder for the amount of 100 pennies
    Then BPL responds with a HTTP 200 and threshold_not_met message
    And the account holder's trenette-accumulator balance is 0
    And 0 issued rewards are available to the account holder

    When BPL receives a transaction for the account holder for the amount of 2000 pennies
    Then BPL receives 2 pending-rewards for trenette-accumulator campaign
    And BPL responds with a HTTP 200 and awarded message
    And 0 issued rewards are available to the account holder
    And the account holder's trenette-accumulator balance is 600

    When BPL receives a transaction for the account holder for the amount of -700 pennies
    Then BPL receives 1 pending-rewards for trenette-accumulator campaign
    And BPL responds with a HTTP 200 and refund_accepted message
    And the account holder's trenette-accumulator balance is 600

    When BPL receives a transaction for the account holder for the amount of -1400 pennies
    Then BPL responds with a HTTP 200 and refund_accepted message
    And the account holder's trenette-accumulator balance is 0
    And BPL receives 0 pending-rewards for trenette-accumulator campaign
    And 0 issued rewards are available to the account holder
