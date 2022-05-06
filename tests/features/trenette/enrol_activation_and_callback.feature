# Created by rupalpatel at 16/02/2022, last updated by Haffi Mazhar at 03/05/2022
Feature: Bink BPL - Ensure a customer can enrol succesfully and that activation and callback is completed
  As a customer
  I want to utilise POST enrol enodpoint
  So I can access to customer management system

  Background:
    Given the trenette retailer exists
    And the retailer's trenette-active-campaign STAMPS campaign starts 10 days ago and ends in a day and is ACTIVE
    And the trenette-active-campaign campaign has an STAMPS earn rule with a threshold of 100, an increment of 0 and a multiplier of 1
    And the trenette-active-campaign campaign has reward rule of 700, with reward slug 10percentoff and allocation window 0
    And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None
    And the retailer has a 10percentoff reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type
    And there is 1 reward configured for the 10percentoff reward config, with allocation status set to false and deleted status set to false


  @bpl @enrol_callback @bpl-302
  Scenario: Enrol account holder successful with callback
    When i Enrol a account holder passing in all required and all optional fields
    Then the account holder is activated
    And new enrolled account holder's trenette-active-campaign balance is 0
    And an enrolment callback task is saved in the database
    And the enrolment-callback task status is success
    And the balance shown for account holder is 0


  @bpl @enrol_callback_retry @bpl-303
  Scenario: Enrol account holder successful with retry
    When an account holder is enrolled passing in all required and optional fields with a callback URL for 2 consecutive HTTP 500 responses
    Then the account holder is activated
    And new enrolled account holder's trenette-active-campaign balance is 0
    And an enrolment callback task is saved in the database
    And the enrolment-callback task status is success
    And the enrolment-callback is retried 2 time and successful on attempt 3
    And a enrolment-callback retryable error is received 2 time with 500 responses
    And the balance shown for account holder is 0
