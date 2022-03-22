# Created by rupalpatel at 22/03/2022
Feature: Transaction with no earn threshold
  As a customer
  There is no earn threshold match set up
  So I make sure that balance get increase whatever i transact

  @transaction_without_threshold @bpl
  Scenario: Transaction with no earn threshold
    Given the trenette retailer exists
    And that retailer has the trenette-acc-campaign-1 campaign configured
    And required fetch type are configured for the current retailer
    And that campaign has the standard reward config configured with 1 allocable rewards
    And an active account holder exists for the retailer
    When BPL receives a transaction for the account holder for the amount of 2000 pennies
    Then the account holder get a HTTP 200 with Awarded response
    And the account holder's trenette-acc-campaign-1 accumulator campaign balance 2000 is updated
    When the account holder send GET accounts request by UUID
    Then the account holder's trenette-acc-campaign-1 balance is 2000
    When BPL receives a transaction for the account holder for the amount of 650 pennies
    Then the account holder's trenette-acc-campaign-1 accumulator campaign balance 2650 is updated

  @transaction_reaching_thresold @bpl
  Scenario: Transaction with no earn threshold reaching reward goal
    Given the trenette retailer exists
    And that retailer has the trenette-acc-campaign-1 campaign configured
    And required fetch type are configured for the current retailer
    And that campaign has the standard reward config configured with 1 allocable rewards
    And an active account holder exists for the retailer
    When BPL receives a transaction for the account holder for the amount of 2000 pennies
    Then the account holder get a HTTP 200 with Awarded response
    And the account holder's trenette-acc-campaign-1 accumulator campaign balance 2000 is updated
    When the account holder send GET accounts request by UUID
    Then the account holder's trenette-acc-campaign-1 balance is 2000
    When BPL receives a transaction for the account holder for the amount of 8000 pennies
    Then the account holder get a HTTP 200 with Awarded response
    When the account holder send GET accounts request by UUID
    Then the account holder's trenette-acc-campaign-1 accumulator campaign balance 0 is updated
