# Created by rupalpatel at 24/02/2022
Feature: Bink BPL - Transaction increases user balance, reward goal met
  As a customer
  I want to transact some amount
  So I make sure that balance get increase and reward goal meet

  @transaction @test
  Scenario Outline: Account holder is rewarded when reward threshold is met
    Given the trenette retailer exists
    And that retailer has the standard campaigns configured
    And required fetch type are configured for the current retailer
    And that campaign has the standard reward config configured with 1 allocable rewards
    And an active account holder exists with the email address test@bink.com for the retailer
    When BPL receives a transaction for the account holder for the amount of <amount_1> pennies
    Then the account holder's trenette-stmp-campaign-1 balance is updated
    When BPL receives a transaction for the account holder for the amount of <amount_2> pennies
    Then the account holder's trenette-stmp-campaign-1 balance is updated
    When BPL receives a transaction for the account holder for the amount of <amount_3> pennies
    Then the account holder's trenette-stmp-campaign-1 balance is updated
    When BPL receives a transaction for the account holder for the amount of <amount_4> pennies
    Then the account holder's trenette-stmp-campaign-1 balance is updated
    When BPL receives a transaction for the account holder for the amount of <amount_5> pennies
    Then the account holder's trenette-stmp-campaign-1 balance is updated
    When BPL receives a transaction for the account holder for the amount of <amount_6> pennies
    Then the account holder's trenette-stmp-campaign-1 balance is updated
    When BPL receives a transaction for the account holder for the amount of <amount_7> pennies
    Then the account holder's trenette-stmp-campaign-1 balance is updated
    When the account holder send GET accounts request by UUID
    Then the account holder issued reward
    And the account holder's trenette-stmp-campaign-1 balance is <final_balance>

    Examples:
      | amount_1 | amount_2 | amount_3 | amount_4 | amount_5 | amount_6 | amount_7 | final_balance |
      | 600      | 570      | 690      | 505      | 610      | 615      | 550      | 0             |
