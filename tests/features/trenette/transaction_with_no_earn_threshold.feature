# Created by rupalpatel at 22/03/2022
Feature: Transaction with no earn threshold
  As a customer
  There is no earn threshold match set up
  So I make sure that balance get increase whatever I transact

  Background:
    Given the trenette retailer exists
    And the retailer's trenette-acc-campaign-1 ACCUMULATOR campaign starts 5 days ago and ends in a day and is ACTIVE
    And the trenette-acc-campaign-1 campaign has an ACCUMULATOR earn rule with a threshold of 0, an increment of 0 and a multiplier of 1
    And the trenette-acc-campaign-1 campaign has reward rule of 10000, with reward slug 10percentoff and allocation window 0
    And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None
    And the retailer has a 10percentoff reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type
    And there is 2 reward configured for the 10percentoff reward config, with allocation status set to false and deleted status set to false

  @transaction @bpl
  Scenario Outline: Transaction with 0 threshold to verify balance and rewards
    Given an active account holder exists for the retailer
    When BPL receives a transaction for the account holder for the amount of <tx_amount_1> pennies
    Then the account holder's trenette-acc-campaign-1 accumulator campaign balance <expected_balance_1> is updated
    And <expected_num_rewards_1> rewards are available to the account holder
    And the account holder's trenette-acc-campaign-1 balance is <expected_balance_1>
    When BPL receives a transaction for the account holder for the amount of <tx_amount_2> pennies
    Then the account holder's trenette-acc-campaign-1 accumulator campaign balance <expected_balance_2> is updated
    And <expected_num_rewards_2> rewards are available to the account holder

    Examples:
      | tx_amount_1 | expected_balance_1 | tx_amount_2 | expected_balance_2 | expected_num_rewards_1 | expected_num_rewards_2 |
      | 2000        | 2000               | 650         | 2650               | 0                      | 0                      |
      | 2000        | 2000               | 8000        | 0                  | 0                      | 1                      |
      | 10000       | 0                  | 10000       | 0                  | 1                      | 2                      |
