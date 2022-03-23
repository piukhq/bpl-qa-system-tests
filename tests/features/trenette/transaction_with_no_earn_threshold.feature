# Created by rupalpatel at 22/03/2022
Feature: Transaction with no earn threshold
  As a customer
  There is no earn threshold match set up
  So I make sure that balance get increase whatever i transact

  @transaction_without_threshold @bpl @test
  Scenario Outline: Transaction with 0 threshold and verify balance and rewards
    Given the trenette retailer exists
    And that retailer has the trenette-acc-campaign-1 campaign configured
    And required fetch type are configured for the current retailer
    And that campaign has the standard reward config configured with 2 allocable rewards
    And an active account holder exists for the retailer
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
