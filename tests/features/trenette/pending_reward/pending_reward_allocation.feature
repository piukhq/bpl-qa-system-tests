# Created by rupalpatel at 13/10/2022
Feature: Bink BPL - Ensure a Pending reward is allocated to account holder when conversion date is reached
  As a customer
  I want to the verify the pending reward get issued
  So that it is clear that i hae earned rewards
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

  @bpl @pending_reward @bpl-765
  Scenario: pending reward is allocated to account holder
    Given an active account holder exists for the retailer
    And the account has 1 pending rewards for the trenette-active-campaign campaign and 10percentoff reward slug with value 700
    When the account's pending rewards conversion date is in 0 days for trenette-active-campaign campaign
    Then the cosmos pending-reward-allocation task status is success
    And the cosmos reward-issuance task status is success
    And 1 issued rewards are available to the account holder for the trenette-active-campaign campaign
