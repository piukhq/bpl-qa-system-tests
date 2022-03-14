# Created by rupalpatel at 24/02/2022
Feature: Bink BPL - Transaction increases user balance, reward goal met
  As a customer
  I want to transact some amount
  So I make sure that balance get increase and reward goal meet

  @transaction @test
  Scenario Outline: Transaction meets earn threshold
    Given the trenette retailer exists
    And that retailer has the standard campaigns configured
    And required fetch type are configured for the current retailer
    And that campaign has the standard reward config configured with 1 allocable rewards
    Then Retailer, Campaigns, and RewardConfigs are successfully created in the database
    When the account holder enrol to retailer with all required and all optional fields
    And an active account holder exists for trenette
    And the account holder POST transaction request for trenette retailer with <amount_1>
    Then the account holder get a HTTP 200 with <response_type> response
    And the account holder's balance is updated
    When the account holder POST transaction request for trenette retailer with <amount_2>
    Then the account holder's balance is updated
    When the account holder POST transaction request for trenette retailer with <amount_3>
    Then the account holder's balance is updated
    When the account holder POST transaction request for trenette retailer with <amount_4>
    Then the account holder's balance is updated
    When the account holder POST transaction request for trenette retailer with <amount_5>
    Then the account holder's balance is updated
    When the account holder POST transaction request for trenette retailer with <amount_6>
    Then the account holder's balance is updated
    When the account holder POST transaction request for trenette retailer with <amount_7>
    Then the account holder's balance is updated
    When the account holder send GET accounts request by UUID
    Then the account holder issued reward
    And the account holder's UUID and account number appearing correct
    And the account holder's balance got adjusted
    And status <status> appeared

    Examples:
      | amount_1 | amount_2 | amount_3 | amount_4 | amount_5 | amount_6 | amount_7 | response_type | status |
      | 600      | 570      | 690      | 505      | 610      | 615      | 550      | Awarded       | active |
