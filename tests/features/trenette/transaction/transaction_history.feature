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
    And there is 5 rewards configured for the free-item reward config, with allocation status set to false and deleted status set to false
    And the retailer has a WELCOME_EMAIL email template configured with template id 99999999
    And the email template with template id 99999999 has the following required template variables: first_name, last_name, account_number, marketing_token


  @bpl @transaction-history-1 @bpl-596
  Scenario: Transaction history with amount
    Given an active account holder exists for the retailer
    And the account holder's trenette-acc-campaign balance is 2000
    Then the account holder's trenette-acc-campaign balance is returned as 2000
    When BPL receives a transaction for the account holder for the amount of 650 pennies
    Then 0 issued rewards are available to the account holder
    And the account holder's trenette-acc-campaign balance is returned as 2650
    Then The account holder's transaction history has 1 transactions, and the latest transaction is 6.50


  @bpl @transaction-history-2 @bpl-596
  Scenario: Transaction history with refund
    Given an active account holder exists for the retailer
    And the account holder's trenette-acc-campaign balance is 2650
    Then the account holder's trenette-acc-campaign balance is returned as 2650
    And 0 issued rewards are available to the account holder
    When BPL receives a transaction for the account holder for the amount of -799 pennies
    Then 0 issued rewards are available to the account holder
    And the account holder's trenette-acc-campaign balance is returned as 1851
    Then The account holder's transaction history has 1 transactions, and the latest transaction is -7.99

  @bpl @transaction-history-3 @bpl-596
  Scenario: Transaction history with maximum 10 record
    Given an active account holder exists for the retailer

    When BPL receives a transaction for the account holder for the amount of 150 pennies
    Then The account holder's transaction history has 1 transactions, and the latest transaction is 1.50

    When BPL receives a transaction for the account holder for the amount of 250 pennies
    Then The account holder's transaction history has 2 transactions, and the latest transaction is 2.50

    When BPL receives a transaction for the account holder for the amount of 350 pennies
    Then The account holder's transaction history has 3 transactions, and the latest transaction is 3.50

    When BPL receives a transaction for the account holder for the amount of 450 pennies
    Then The account holder's transaction history has 4 transactions, and the latest transaction is 4.50

    When BPL receives a transaction for the account holder for the amount of 550 pennies
    Then The account holder's transaction history has 5 transactions, and the latest transaction is 5.50

    When BPL receives a transaction for the account holder for the amount of 650 pennies
    Then The account holder's transaction history has 6 transactions, and the latest transaction is 6.50

    When BPL receives a transaction for the account holder for the amount of 750 pennies
    Then The account holder's transaction history has 7 transactions, and the latest transaction is 7.50

    When BPL receives a transaction for the account holder for the amount of 850 pennies
    Then The account holder's transaction history has 8 transactions, and the latest transaction is 8.50

    When BPL receives a transaction for the account holder for the amount of 950 pennies
    Then The account holder's transaction history has 9 transactions, and the latest transaction is 9.50

    When BPL receives a transaction for the account holder for the amount of 1050 pennies
    Then The account holder's transaction history has 10 transactions, and the latest transaction is 10.50

    When BPL receives a transaction for the account holder for the amount of -210 pennies
    Then The account holder's transaction history has 10 transactions, and the latest transaction is -2.10

    When BPL receives a transaction for the account holder for the amount of -310 pennies
    Then The account holder's transaction history has 10 transactions, and the latest transaction is -3.10

  @bpl @transaction-history-4 @bpl-596
  Scenario: Transaction history with amount showing for getbycredential
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

  @bpl @transaction-history-5 @bpl-596
  Scenario: Number of transactions to appear for transaction history - For get by credential POST call
    Given an active account holder exists for the retailer


    When BPL receives a transaction for the account holder for the amount of 150 pennies
    Then The account holder's transaction history has 1 transactions, and the latest transaction is 1.50

    When BPL receives a transaction for the account holder for the amount of 250 pennies
    Then The account holder's transaction history has 2 transactions, and the latest transaction is 2.50

    When BPL receives a transaction for the account holder for the amount of 350 pennies
    Then The account holder's transaction history has 3 transactions, and the latest transaction is 3.50

    When BPL receives a transaction for the account holder for the amount of 450 pennies
    Then The account holder's transaction history has 4 transactions, and the latest transaction is 4.50

    And BPL set up to receive only 3 recent transaction appeared into transaction history with get by credential for the account holder

    When BPL receives a transaction for the account holder for the amount of 550 pennies
    Then The account holder's transaction history has 5 transactions, and the latest transaction is 5.50

    And BPL set up to receive only 4 recent transaction appeared into transaction history with get by credential for the account holder

  @bpl @transaction_history-6 @bpl-596
  Scenario: Number of transactions to appear for transaction history - For get account GET call
    Given an active account holder exists for the retailer


    When BPL receives a transaction for the account holder for the amount of 150 pennies
    Then The account holder's transaction history has 1 transactions, and the latest transaction is 1.50

    When BPL receives a transaction for the account holder for the amount of 250 pennies
    Then The account holder's transaction history has 2 transactions, and the latest transaction is 2.50

    When BPL receives a transaction for the account holder for the amount of 350 pennies
    Then The account holder's transaction history has 3 transactions, and the latest transaction is 3.50

    When BPL receives a transaction for the account holder for the amount of 450 pennies
    Then The account holder's transaction history has 4 transactions, and the latest transaction is 4.50

    And BPL set up to receive only 3 recent transaction appeared into transaction history with get by account for the account holder

    When BPL receives a transaction for the account holder for the amount of 550 pennies
    Then The account holder's transaction history has 5 transactions, and the latest transaction is 5.50

    And BPL set up to receive only 4 recent transaction appeared into transaction history with get by account for the account holder