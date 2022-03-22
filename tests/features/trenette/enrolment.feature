@trenette
Feature: Enrol with Trenette loyalty

  Scenario: Successful adding retailer
    Given the trenette retailer exists
    And that retailer has the trenette-stmp-campaign-1 campaign configured
    And required fetch type are configured for the current retailer
    And that campaign has the standard reward config configured with 1 allocable rewards
    And an active account holder exists for the retailer
    Then Retailer, Campaigns, and RewardConfigs are successfully created in the database
