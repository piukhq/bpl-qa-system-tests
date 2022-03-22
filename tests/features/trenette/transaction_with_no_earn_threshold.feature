# Created by rupalpatel at 22/03/2022
Feature: Transaction with no earn threshold
  As a customer
  There is no earn threshold match set up
  So I make sure that balance get increase whatever i transact

  @transaction_without_threshold @bpl
  Scenario Outline: Transaction with no earn threshold
    Given the trenette retailer exists
    And that retailer has the trenette-acc-campaign-1 campaign configured
    And required fetch type are configured for the current retailer
    And that campaign has the standard reward config configured with 1 allocable rewards
    And an active account holder exists for the retailer
    When BPL receives a transaction for the account holder for the amount of <amount_1> pennies
    Then the account holder get a HTTP 200 with <response_type> response
    And the account holder's trenette-acc-campaign-1 accumulator campaign balance for <amount_1> is updated
    When the account holder send GET accounts request by UUID
    Then the account holder's trenette-acc-campaign-1 balance is <amount_1>
    When BPL receives a transaction for the account holder for the amount of <amount_2> pennies
    Then the account holder's trenette-acc-campaign-1 accumulator campaign balance for <final_balance> is updated

    Examples:
      | amount_1 | amount_2 | final_balance | response_type |
      | 2000     | 650      | 2650          | Awarded       |


  @transaction_reaching_thresold @bpl
  Scenario Outline: Transaction with no earn threshold reaching reward goal
    Given the trenette retailer exists
    And that retailer has the trenette-acc-campaign-1 campaign configured
    And required fetch type are configured for the current retailer
    And that campaign has the standard reward config configured with 1 allocable rewards
    And an active account holder exists for the retailer
    When BPL receives a transaction for the account holder for the amount of <amount_1> pennies
    Then the account holder get a HTTP 200 with <response_type> response
    And the account holder's trenette-acc-campaign-1 accumulator campaign balance for <amount_1> is updated
    When the account holder send GET accounts request by UUID
    Then the account holder's trenette-acc-campaign-1 balance is <amount_1>
    When BPL receives a transaction for the account holder for the amount of <amount_2> pennies
    Then the account holder get a HTTP 200 with <response_type> response
    When the account holder send GET accounts request by UUID
    Then the account holder's trenette-acc-campaign-1 accumulator campaign balance for <final_balance> is updated

    Examples:
      | amount_1 | amount_2 | final_balance | response_type |
      | 2000     | 8000     | 0             | Awarded       |