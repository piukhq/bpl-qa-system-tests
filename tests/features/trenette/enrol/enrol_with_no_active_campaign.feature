# Created by rupalpatel at 06/06/2022
Feature: Bink BPL - Ensure a customer can enrol successfully and activation started
    As a customer
    I want to utilise POST enrolment endpoint for account holder
    So I can access to customer management system

    @bpl @enrol_callback @bpl-305 @bpl-305-1
    Scenario: Enrolment Trigger - No active campaign
        Given the trenette retailer exists with status as TEST
        And the retailer has a WELCOME_EMAIL email template configured with template id 99999999
        And the email template with template id 99999999 has the following required template variables: first_name, last_name, account_number, marketing_token
        And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None
        And the retailer has a 10percentoff reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type

        And the retailer's trenette-campaign STAMPS campaign starts 10 days ago and ends in a day and is DRAFT
        And the trenette-campaign campaign has an earn rule with a threshold of 500, an increment of 100, a multiplier of 1 and max amount of 0
        And the trenette-campaign campaign has reward rule with reward goal: 700, allocation window: 0 and reward cap: 0

        And 5 unassigned rewards are generated for the 10percentoff reward config with deleted status set to false
        And I enrol an account holder passing in all required and all optional fields

        Then the account holder activation is started
        And an enrolment callback task is saved in the database
        And the polaris account-holder-activation task status is success
        And the polaris send-email task status is success
        And the polaris enrolment-callback task status is success
        And the account holder's trenette-campaign balance does not exist


    @bpl @enrol_callback @bpl-305 @bpl-305-2
    Scenario: Enrolment Trigger - Draft campaign activated
        Given the trenette retailer exists with status as TEST
        And the retailer has a WELCOME_EMAIL email template configured with template id 99999999
        And the email template with template id 99999999 has the following required template variables: first_name, last_name, account_number, marketing_token
        And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None
        And the retailer has a 10percentoff reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type

        And the retailer's trenette-campaign STAMPS campaign starts 10 days ago and ends in a day and is DRAFT
        And the trenette-campaign campaign has an earn rule with a threshold of 500, an increment of 100, a multiplier of 1 and max amount of 0
        And the trenette-campaign campaign has reward rule with reward goal: 700, allocation window: 0 and reward cap: 0

        And 5 unassigned rewards are generated for the 10percentoff reward config with deleted status set to false
        And I enrol an account holder passing in all required and all optional fields

        When the retailer's trenette-campaign campaign status is changed to active
        Then the vela create-campaign-balances task status is success
        And the account holder is activated
        And the account holder balance shown for trenette-campaign is 0
        And the polaris account-holder-activation task status is success
        And the polaris send-email task status is success
        And the polaris enrolment-callback task status is success

    @bpl @bpl-849
    Scenario: Enrolment Trigger - No campaign
        Given the trenette retailer exists with status as TEST
        And the retailer has a WELCOME_EMAIL email template configured with template id 99999999
        And the email template with template id 99999999 has the following required template variables: first_name, last_name, account_number, marketing_token
        And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None

        And I enrol an account holder passing in all required and all optional fields

        Then the account holder activation is started
        And an enrolment callback task is saved in the database
        And the polaris account-holder-activation task status is success
        And the polaris send-email task status is success
        And the polaris enrolment-callback task status is success
        And the account holder's trenette-campaign balance does not exist


