# Created by rupalpatel at 12/07/2022
Feature: Bink BPL - Transaction history
  As a customer
  I want to transact some amount
  So I make sure that transaction history record showing as expected

  Background:
    Given the trenette retailer exists
    And the retailer's trenette-acc-campaign ACCUMULATOR campaign starts 5 days ago and ends in a day and is ACTIVE
    And the trenette-acc-campaign campaign has an earn rule with a threshold of 0, an increment of 100, a multiplier of 1 and max amount of 0
    And the trenette-acc-campaign campaign has reward rule of 10000, with reward slug free-item and allocation window 1
    And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None
    And the retailer has a free-item reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type
    And there is 5 reward configured for the free-item reward config, with allocation status set to false and deleted status set to false
    And the retailer has a WELCOME_EMAIL email template configured with template id template-id and first_name, last_name, account_number, marketing_token variables


  @bpl @transaction_history-1 @bpl-596
  Scenario: Transaction history table with amount showing
    Given an active account holder exists for the retailer
    And the account holder's trenette-acc-campaign balance is 2000
    Then the account holder's trenette-acc-campaign balance is returned as 2000
    When BPL receives a transaction for the account holder for the amount of 650 pennies
    Then 0 issued rewards are available to the account holder
    And the account holder's trenette-acc-campaign balance is returned as 2650
    And there is 1 transaction record with amount 6.50 for ACCUMULATOR campaign

  @bpl @transaction_history-2 @bpl-596
  Scenario: Transaction history table with refund showing
    Given an active account holder exists for the retailer
    And the account holder's trenette-acc-campaign balance is 2650
    Then the account holder's trenette-acc-campaign balance is returned as 2650
    And 0 issued rewards are available to the account holder
    When BPL receives a transaction for the account holder for the amount of -799 pennies
    Then 0 issued rewards are available to the account holder
    And the account holder's trenette-acc-campaign balance is returned as 1851
    And there is 1 transaction record with amount -7.99 for ACCUMULATOR campaign

  @bpl @transaction_history-3 @bpl-596
  Scenario: Transaction history table with maximum 10 record showing
    Given an active account holder exists for the retailer

    When BPL receives a transaction for the account holder for the amount of 150 pennies
    Then there is 1 transaction record with amount 1.50 for ACCUMULATOR campaign

    When BPL receives a transaction for the account holder for the amount of 250 pennies
    Then there is 2 transaction record with amount 2.50 for ACCUMULATOR campaign
    When BPL receives a transaction for the account holder for the amount of 350 pennies
    Then there is 3 transaction record with amount 3.50 for ACCUMULATOR campaign
    When BPL receives a transaction for the account holder for the amount of 450 pennies
    Then there is 4 transaction record with amount 4.50 for ACCUMULATOR campaign
    When BPL receives a transaction for the account holder for the amount of 550 pennies
    Then there is 5 transaction record with amount 5.50 for ACCUMULATOR campaign
    When BPL receives a transaction for the account holder for the amount of 650 pennies
    Then there is 6 transaction record with amount 6.50 for ACCUMULATOR campaign
    When BPL receives a transaction for the account holder for the amount of 750 pennies
    Then there is 7 transaction record with amount 7.50 for ACCUMULATOR campaign
    When BPL receives a transaction for the account holder for the amount of 850 pennies
    Then there is 8 transaction record with amount 8.50 for ACCUMULATOR campaign
    When BPL receives a transaction for the account holder for the amount of 950 pennies
    Then there is 9 transaction record with amount 9.50 for ACCUMULATOR campaign
    When BPL receives a transaction for the account holder for the amount of 1050 pennies
    Then there is 10 transaction record with amount 10.50 for ACCUMULATOR campaign

    When BPL receives a transaction for the account holder for the amount of -210 pennies
    Then there is 10 transaction record with amount -2.10 for ACCUMULATOR campaign

    When BPL receives a transaction for the account holder for the amount of -310 pennies
    Then there is 10 transaction record with amount -3.10 for ACCUMULATOR campaign

  @bpl @transaction_history-4 @bpl-596
  Scenario: Transaction history table with amount showing for getbycredential
    Given an active account holder exists for the retailer

    When BPL receives a transaction for the account holder for the amount of 150 pennies
    And BPL receives a transaction for the account holder for the amount of 250 pennies
    And BPL receives a transaction for the account holder for the amount of 350 pennies
    And BPL receives a transaction for the account holder for the amount of 450 pennies
    And BPL receives a transaction for the account holder for the amount of 550 pennies
    And BPL receives a transaction for the account holder for the amount of 650 pennies
    And BPL receives a transaction for the account holder for the amount of 750 pennies
    And BPL receives a transaction for the account holder for the amount of 850 pennies
    And BPL receives a transaction for the account holder for the amount of 950 pennies
    And BPL receives a transaction for the account holder for the amount of 1050 pennies

    Then there is 10 transaction history in array
    When BPL receives a transaction for the account holder for the amount of 1050 pennies
    Then there is 10 transaction history in array