Feature: Bink BPL - Campaign is set to cancelled and reward is not allocated
  As a customer
  I want to transact some amount with two campaigns, so they both meet the reward goal
  and then change of the campaigns to cancelled, so that the reward is not allocated

  Background:
    Given the trenette retailer exists
    And the retailer's trenette-stmp-campaign-1 STAMPS campaign starts 5 days ago and ends in a day and is ACTIVE
    And the retailer's trenette-stmp-campaign-2 STAMPS campaign starts 5 days ago and ends in a day and is ACTIVE
    And the trenette-stmp-campaign-1 campaign has an STAMPS earn rule with a threshold of 500, an increment of 100 and a multiplier of 1
    And the trenette-stmp-campaign-2 campaign has an STAMPS earn rule with a threshold of 500, an increment of 100 and a multiplier of 1
    And the trenette-stmp-campaign-1 campaign has reward rule of 100, with reward slug free-item and allocation window 0
    And the trenette-stmp-campaign-2 campaign has reward rule of 100, with reward slug free-item-2 and allocation window 0
    And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None with an agent config of None
    And the retailer has a free-item reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type
    And the retailer has a free-item-2 reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type
    And there is 1 reward configured for the free-item reward config, with allocation status set to false and deleted status set to false
    And there is 1 reward configured for the free-item-2 reward config, with allocation status set to false and deleted status set to false

  @bpl @transaction @bpl-298
  Scenario: Transaction meets earn threshold for two campaigns and one campaign is cancelled
    Given an active account holder exists for the retailer
    When BPL receives a transaction for the account holder for the amount of 600 pennies
    Then the account holder's trenette-stmp-campaign-1 balance is reduced by the reward goal
    And the status is then changed to cancelled for trenette-stmp-campaign-1 for the retailer trenette
    And the trenette account is not issued reward free-item
    And the account holder's trenette-stmp-campaign-1 balance no longer exists