# Created by rupalpatel at 23/03/2022
Feature: Bink BPL - Transaction doesn't meet threshold
  As a customer
  I am doing transaction with less then threshold amount
  So I make sure that I dont get reward or balance increament

  Background:
    Given the trenette retailer exists
    And that retailer has the <campaign_type> campaign configured
    And required fetch type are configured for the current retailer
    And that campaign has the standard reward config configured with 1 allocable rewards

  @bpl @transaction @test
  Scenario Outline: Transaction doesn’t qualify for earn
    Given an active account holder exists for the retailer
    When BPL receives a transaction for the account holder for the amount of 480 pennies
    Then BPL responds with a HTTP 200 and threshold_not_met message
    And the account holder's <campaign_type> balance is 0
    And 0 rewards are available to the account holder

    Examples:
      | campaign_type            |
      | trenette-stmp-campaign-1 |
      | trenette-acc-campaign-3  |

  @bpl @transaction @test
  Scenario Outline: Account holder already has balance but new transaction isn't qualify for earn and balance
    Given an active account holder exists for the retailer
    When BPL receives a transaction for the account holder for the amount of <transaction_amount_1> pennies
    Then <expected_reward> rewards are available to the account holder
    And the account holder's <campaign_type> balance is <expected_balance>
    When BPL receives a transaction for the account holder for the amount of <transaction_amount_2> pennies
    Then BPL responds with a HTTP 200 and threshold_not_met message
    And the account holder's <campaign_type> balance is <expected_balance>
    And <expected_reward> rewards are available to the account holder

    Examples:
      | campaign_type            | transaction_amount_1 | transaction_amount_2 | expected_balance | expected_reward |
      | trenette-stmp-campaign-1 | 770                  | 480                  | 100              | 0               |
      | trenette-acc-campaign-3  | 1100                 | 480                  | 100              | 1               |


