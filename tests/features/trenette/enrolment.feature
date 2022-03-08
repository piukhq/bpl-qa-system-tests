@trenette
Feature: Enrol with Trenette loyalty

    Scenario: Successful adding retailer

        Given the trenette retailer exists
        And That retailer has the standard campaigns configured
#        And and i setup the fetch type
        And That campaign has the standard reward config configured with 4 allocable rewards
        Then Retailer, Campaigns, and RewardConfigs are successfully created in the database
