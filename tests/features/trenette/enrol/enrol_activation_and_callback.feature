# Created by rupalpatel at 16/02/2022, last updated by Haffi Mazhar at 03/05/2022
Feature: Bink BPL - Ensure a customer can enrol successfully and that activation and callback is completed
  As a customer
  I want to utilise POST enrol endpoint
  So I can access to customer management system

  Background:
    Given the trenette retailer exists with status as TEST
    And the retailer has a WELCOME_EMAIL email template configured with template id 99999999
    And the email template with template id 99999999 has the following required template variables: first_name, last_name, account_number, marketing_token
    And the retailer's trenette-active-campaign STAMPS campaign starts 10 days ago and ends in a day and is ACTIVE

  @bpl @enrol_callback @bpl-302
  Scenario: Enrol account holder successful with callback
    When I enrol an account holder passing in all required and all optional fields
    Then the account holder is activated
    And the account holder balance shown for trenette-active-campaign is 0
    And an enrolment callback task is saved in the database
    And the cosmos enrolment-callback task status is success
    And the account holder balance shown for trenette-active-campaign is 0


  @bpl @enrol_callback_retry @bpl-303
  Scenario: Enrol account holder successful with retry
    When an account holder is enrolled passing in all required and optional fields with a callback URL for 2 consecutive HTTP 500 responses
    Then the account holder is activated
    And the account holder balance shown for trenette-active-campaign is 0
    And an enrolment callback task is saved in the database
    And the cosmos enrolment-callback task status is success
    And the enrolment-callback is retried 2 time and successful on attempt 3
    And a enrolment-callback retryable error is received 2 time with 500 responses
    And the account holder balance shown for trenette-active-campaign is 0
