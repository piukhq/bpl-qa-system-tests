# Created by rupalpatel at 24/02/2022
Feature: Bink BPL - Transaction increases user balance, reward goal met
  As a customer
  I want to transact some amount
  So I make sure that balance get increase and reward goal meet

  @transaction @test
  Scenario Outline: Transaction meets earn threshold
    Given The trenette retailer exists
    And That retailer has the standard campaigns configured
    And Required fetch type are configured for the current retailer
    And That campaign has the standard reward config configured with 1 allocable rewards
    When The account holder enrol to retailer with all required and all optional fields
    And An active account holder exists for trenette
    And The account holder POST transaction request for trenette retailer with <amount_1>
    Then The account holder get a HTTP 200 with <response_type> response
    And The account holder's balance is updated
    When The account holder POST transaction request for trenette retailer with <amount_2>
    Then The account holder's balance is updated
    When The account holder POST transaction request for trenette retailer with <amount_3>
    Then The account holder's balance is updated
    When The account holder POST transaction request for trenette retailer with <amount_4>
    Then The account holder's balance is updated
    When The account holder POST transaction request for trenette retailer with <amount_5>
    Then The account holder's balance is updated
    When The account holder POST transaction request for trenette retailer with <amount_6>
    Then The account holder's balance is updated
    When The account holder POST transaction request for trenette retailer with <amount_7>
    Then The account holder's balance is updated
    When The account holder send GET accounts request by UUID
    Then The account holder issued reward
    And The account holder's UUID and account number appearing correct
    And The account holder's balance got adjusted
    And status <status> appeared

    Examples:
      | amount_1 | amount_2 | amount_3 | amount_4 | amount_5 | amount_6 | amount_7 | response_type | status |
      | 600      | 570      | 690      | 505      | 610      | 615      | 550      | Awarded       | active |
