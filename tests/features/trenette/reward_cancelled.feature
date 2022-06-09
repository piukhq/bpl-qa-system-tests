Feature: Reward code status updated to cancelled from 3rd party
  As a retailer
  I want to be able to provide new rewards for cancelled
  so that customers can get cancelled rewards in their account

  Background:
    Given the trenette retailer exists
    And the retailer's trenette-acc-campaign-1 ACCUMULATOR campaign starts 5 days ago and ends in a day and is ACTIVE
    And the trenette-acc-campaign-1 campaign has an ACCUMULATOR earn rule with a threshold of 100, an increment of 0, a multiplier of 1 and max amount of 0
    And the trenette-acc-campaign-1 campaign has reward rule of 700, with reward slug 10percentoff and allocation window 0
    And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None
    And the retailer has a 10percentoff reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type
    And there is 1 reward configured for the 10percentoff reward config, with allocation status set to false and deleted status set to false

  @reward @bpl @bpl_300
  Scenario: Handle importing cancelled reward codes from a 3rd party
    Given an active account holder exists for the retailer
    When BPL receives a transaction for the account holder for the amount of 701 pennies
    Then the account holder's trenette-acc-campaign-1 balance is 1
    And 1 issued rewards are available to the account holder
    When the file for trenette with cancelled status is imported
    Then the file is moved to the archive container by the reward importer
    And the status of the allocated account holder for trenette rewards are updated with CANCELLED
    And 1 reward for the account holder shows as cancelled with redeemed date
