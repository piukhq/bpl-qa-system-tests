# Created by rupalpatel at 06/06/2022
Feature: Bink BPL - Ensure a customer can enrol successfully and activation started
  As a customer
  I want to utilise POST enrolment endpoint for account holder
  So I can access to customer management system


  @bpl @enrol_callback @bpl-305
  Scenario: Enrolment Trigger - No active campaign (draft and then activate)
    Given the trenette retailer exists
    And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None

    And the retailer's trenette-active-campaign STAMPS campaign starts 10 days ago and ends in a day and is DRAFT
    And the trenette-active-campaign campaign has an STAMPS earn rule with a threshold of 500, an increment of 100 and a multiplier of 1
    And the trenette-active-campaign campaign has reward rule of 700, with reward slug 10percentoff and allocation window 0
    And the retailer has a 10percentoff reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type
    And there is 5 reward configured for the 10percentoff reward config, with allocation status set to false and deleted status set to false

    When i Enrol a account holder passing in all required and all optional fields
    Then the account holder activation is started
    And an enrolment callback task is saved in the database
    And the account-holder-activation task status is waiting
    And the send-welcome-email task status is pending
    And the enrolment-callback task status is pending

    Then the status is then changed to active for trenette-active-campaign for the retailer trenette
    When the create-campaign-balances task status is success
    Then the account holder is activated
    And new enrolled account holder's trenette-active-campaign balance is 0
    And the account-holder-activation task status is success
    And the send-welcome-email task status is success
    And the enrolment-callback task status is success


