# Created by rupalpatel at 04/11/2022
Feature: Bink BPL - Activity enrolment
  As a customer
  I want to the enrol with retailer
  So that activity should appear
  Background:
    Given the trenette retailer exists with status as TEST
    And the retailer has a WELCOME_EMAIL email template configured with template id 99999999
    And the email template with template id 99999999 has the following required template variables: first_name, last_name, account_number, marketing_token

    And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None
    And the retailer has a 10percentoff reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type

    And the retailer's trenette-active-campaign ACCUMULATOR campaign starts 10 days ago and ends in a day and is ACTIVE
    And the trenette-active-campaign campaign has an earn rule with a threshold of 500, an increment of 100, a multiplier of 1 and max amount of 0
    And the trenette-active-campaign campaign has reward rule with reward goal: 700, allocation window: 1 and reward cap: 0

    And 2 unassigned rewards are generated for the 10percentoff reward config with deleted status set to false

  @bpl-722 @accepted @bpl
  Scenario: Activity for enrolment request
    When I enrol an account holder passing in all required and all optional fields
    Then the account holder is activated
    And there is ACCOUNT_REQUEST activity appeared
    And ACCOUNT_REQUEST activity has result field result as Accepted

  @bpl-722 @account_exist @bpl
  Scenario: Activity for duplicate enrolment request
    When I enrol a same account holder again
    Then the account holder is activated
    And there is ACCOUNT_REQUEST activity appeared
    And ACCOUNT_REQUEST activity has result field result as ACCOUNT_EXISTS

  @bpl-722 @missing_field @bpl
  Scenario: Activity for enrolment request without email
    When I enrol an account holder without email field
    Then there is ACCOUNT_REQUEST activity appeared
    And ACCOUNT_REQUEST activity has result field result as FIELD_VALIDATION_ERROR
