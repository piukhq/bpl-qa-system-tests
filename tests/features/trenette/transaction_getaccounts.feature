# Created by rupalpatel at 24/02/2022
Feature: Bink BPL - Transaction increases user balance, reward goal met
  As a customer
  I want to transact some amount
  So I make sure that balance get increase and reward goal meet

  @transaction @test
  Scenario Outline: Transaction meets earn threshold
    Given The trenette retailer exists
    And That retailer has the standard campaigns configured
    And Retailer setup the fetch type
    And That campaign has the standard reward config configured with 4 allocable rewards
    When The account holder enrol to trenette retailer with all required and all optional fields
    And A active account holder exists for trenette
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
#    And The account holder's balance is updated

    Examples:
      | amount_1 | amount_2 | amount_3 | amount_4 | amount_5 | amount_6 | amount_7 | response_type |
      | 600      | 570      | 690      | 505      | 610      | 615      | 550      | Awarded       |

  #      | amount_1 | response_type |
#      | 600      | Awarded       |

#  @getaccount
#  Scenario Outline: GET on account shows issued reward for campaign
#    Given The trenette retailer exists
#    And That retailer has the standard campaigns configured
#    And That retailer has the standard reward config configured with 4 allocable rewards
#    And The active campaign has an active account holder with a balance of <balance>
#    When The account holder send a POST transaction request with <amount>
#    Then The account holder get a HTTP 200 response
#    When The account holder send GET account_id
#    Then The issued reward is displayed
#    And The account holder's balance is updated
#
#    Examples:
#      | balance | amount |
#      | 6       | 600    |


