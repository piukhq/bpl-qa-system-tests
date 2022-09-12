# Created by rupalpatel at 16/06/2022
Feature: Bink BPL - Jigshaw egift - Transaction increases user balance
  As a customer
  I am doing transaction to asos egift and it meets earn threshold
  So I make sure that I got balance increased

  @bpl @asos @transaction @bpl-571
  Scenario: jigshaw egift - Transaction meets earn threshold (>0)

    Given the asos retailer exists
    And the retailer's asos-campaign ACCUMULATOR campaign starts 5 days ago and ends in a day and is ACTIVE
    And the asos-campaign campaign has an earn rule with a threshold of 0, an increment of 100, a multiplier of 1 and max amount of 0
    And the asos-campaign campaign has reward rule of 10000, with reward slug free-item and allocation window 0
    And a JIGSAW_EGIFT fetch type is configured for the current retailer with an agent config brand id 30
    And the retailer has a free-item reward config configured with transaction_value: 10, and a status of ACTIVE and a JIGSAW_EGIFT fetch type
    And there is 2 rewards configured for the free-item reward config, with allocation status set to false and deleted status set to false

    And an active account holder exists for the retailer
    When BPL receives a transaction for the account holder for the amount of 5500 pennies
    Then 0 issued rewards are available to the account holder
    And the account holder's asos-campaign balance is returned as 5500
    When BPL receives a transaction for the account holder for the amount of 6000 pennies
    Then 1 issued rewards are available to the account holder
    And the account holder's asos-campaign balance is returned as 1500
