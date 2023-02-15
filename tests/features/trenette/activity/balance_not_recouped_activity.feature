# Created by rupalpatel at 09/11/2022
Feature: Bink BPL - Activity balance not recouped
  As a customer
  I refund some amount which not recouped
  So that activity should appear
  Background:
    Given the trenette retailer exists with status as TEST
    And the retailer has a WELCOME_EMAIL email template configured with template id 99999999
    And the email template with template id 99999999 has the following required template variables: first_name, last_name, account_number, marketing_token

    And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None
    And the retailer has a 10percentoff reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type

    And the retailer's trenette-active-campaign ACCUMULATOR campaign starts 10 days ago and ends in a day and is ACTIVE
    And the trenette-active-campaign campaign has an earn rule with a threshold of 500, an increment of None, a multiplier of 1 and max amount of 0
    And the trenette-active-campaign campaign has reward rule with reward goal: 1000, allocation window: 2 and reward cap: 0

    And 2 unassigned rewards are generated for the 10percentoff reward config with deleted status set to false

  @bpl-706 @balance_recouped @bpl @bpl-2.0
  Scenario: Activity for balance not recouped - pending reward
    Given an active account holder exists for the retailer
    When BPL receives a transaction for the account holder for the amount of 1000 pennies
    Then the account holder balance shown for trenette-active-campaign is 0
    And 1 pending rewards are available to the account holder for the trenette-active-campaign campaign
    When BPL receives a transaction for the account holder for the amount of -1098 pennies
    Then BPL responds with a HTTP 200 and refund_accepted message
    And the account holder balance shown for trenette-active-campaign is 0
    And 0 pending rewards are available to the account holder for the trenette-active-campaign campaign
    Then there is REFUND_NOT_RECOUPED activity appeared
