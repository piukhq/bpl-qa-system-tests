# Created by rupalpatel at 24/02/2022
Feature: Bink BPL - Transaction increases user balance, reward goal met
  As a customer
  I want to transact some amount
  So I make sure that balance get increase and reward goal meet

  Background:
    Given the trenette retailer exists
    And the retailer's trenette-stmp-campaign STAMPS campaign starts 5 days ago and ends in a day and is ACTIVE
    And the trenette-stmp-campaign campaign has an STAMPS earn rule with a threshold of 500, an increment of 100 and a multiplier of 1
    And the trenette-stmp-campaign campaign has reward rule of 700, with reward slug free-item and allocation window 0
    And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None
    And the retailer has a free-item reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type
    And there is 1 reward configured for the free-item reward config, with allocation status set to false and deleted status set to false

  @transaction @bpl
  Scenario Outline: Account holder is rewarded when reward threshold is met
    Given an active account holder exists for the retailer
    When BPL receives a transaction for the account holder for the amount of <amount_1> pennies
    Then the account holder's trenette-stmp-campaign balance is 100
    When BPL receives a transaction for the account holder for the amount of <amount_2> pennies
    Then the account holder's trenette-stmp-campaign balance is 200
    When BPL receives a transaction for the account holder for the amount of <amount_3> pennies
    Then the account holder's trenette-stmp-campaign balance is 300
    When BPL receives a transaction for the account holder for the amount of <amount_4> pennies
    Then the account holder's trenette-stmp-campaign balance is 400
    When BPL receives a transaction for the account holder for the amount of <amount_5> pennies
    Then the account holder's trenette-stmp-campaign balance is 500
    When BPL receives a transaction for the account holder for the amount of <amount_6> pennies
    Then the account holder's trenette-stmp-campaign balance is 600
    When BPL receives a transaction for the account holder for the amount of <amount_7> pennies
    Then the account holder's trenette-stmp-campaign balance is 0
    And 1 rewards are available to the account holder

    Examples:
      | amount_1 | amount_2 | amount_3 | amount_4 | amount_5 | amount_6 | amount_7 |
      | 600      | 570      | 690      | 505      | 610      | 615      | 550      |
      | 1700     | 1550     | 1505     | 1610     | 1605     | 1700     | 1050     |