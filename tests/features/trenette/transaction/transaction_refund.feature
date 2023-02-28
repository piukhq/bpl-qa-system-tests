# Created by rupalpatel at 23/05/2022
Feature: Bink BPL - refund
  As a customer
  I want to transact some negative amount
  So I make sure that balance and pending window should updated

  Background:
    Given the trenette retailer exists with status as TEST
    And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None
    And the retailer has a free-item reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type
    And the retailer has a REWARD_ISSUANCE email template configured with template id 99999999
    And the email template with template id 99999999 has the following required template variables: reward_url, account_number, first_name

    And the retailer's trenette-accumulator ACCUMULATOR campaign starts 5 days ago and ends in a day and is ACTIVE
    And the trenette-accumulator campaign has an earn rule with a threshold of 200, an increment of 100, a multiplier of 1 and max amount of 0
    And the trenette-accumulator campaign has reward rule with reward goal: 700, allocation window: 1 and reward cap: 0

    And 1 unassigned rewards are generated for the free-item reward config with deleted status set to false

  @bpl @transaction @refund @bpl-540 @bpl-2.0
  Scenario: Refund accepted and balance updated with 0
    Given an active account holder exists for the retailer

    When BPL receives a transaction for the account holder for the amount of 2000 pennies

    Then BPL responds with a HTTP 200 and awarded message
    And 2 pending rewards are available to the account holder for the trenette-accumulator campaign
    And the account holder balance shown for trenette-accumulator is 600

    When BPL receives a transaction for the account holder for the amount of -700 pennies
    Then BPL responds with a HTTP 200 and refund_accepted message
    And the account holder balance shown for trenette-accumulator is 600
    And 1 pending rewards are available to the account holder for the trenette-accumulator campaign

    When BPL receives a transaction for the account holder for the amount of -1400 pennies
    Then BPL responds with a HTTP 200 and refund_accepted message
    And the account holder balance shown for trenette-accumulator is 0
    And 0 pending rewards are available to the account holder for the trenette-accumulator campaign
