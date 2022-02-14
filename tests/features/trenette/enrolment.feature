@trenette @bpl
Feature: Enrol with Trenette loyalty

    Scenario: Successful enrolment

        Given the trenette retailer exists
        And has the standard campaigns configured
        And has the standard reward config configured with 4 allocable rewards
        Then Retailer, Campaigns, and RewardConfigs are successfully created in the database
