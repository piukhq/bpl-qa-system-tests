# Created by rupalpatel at 17/11/2022
Feature: Bink BPL - Activity pending reward- total cost to user affected by refund
  As a customer
  I refund some amount which changes total cost to user
  So that activity should appear
  Background:
    Given the trenette retailer exists with status as TEST
    And the retailer has a WELCOME_EMAIL email template configured with template id 99999999
    And the email template with template id 99999999 has the following required template variables: first_name, last_name, account_number, marketing_token

    And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None
    And the retailer's trenette-active-campaign ACCUMULATOR campaign starts 10 days ago and ends in a day and is ACTIVE
    And the retailer's trenette-active-campaign campaign with reward_slug: 10percentoff added as ACTIVE
    And the trenette-active-campaign campaign has an earn rule with a threshold of 500, an increment of None, a multiplier of 1 and max amount of 0
    And the trenette-active-campaign campaign has reward rule with reward goal: 1000, reward slug: 10percentoff, allocation window: 2 and reward cap: 2
    And the retailer has a 10percentoff reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type
    And there is 2 rewards configured for the 10percentoff reward config, with allocation status set to false and deleted status set to false

  @bpl-734-1 @bpl-734 @bpl
  Scenario: REWARD_UPDATE activity created when we process refund [slush=refund]
    Given an active account holder exists for the retailer
    When BPL receives a transaction for the account holder for the amount of 3333 pennies
    Then the account holder balance shown for trenette-active-campaign is 0
    And 2 pending rewards are available to the account holder for the trenette-active-campaign campaign
    When BPL receives a transaction for the account holder for the amount of -1333 pennies
    Then BPL responds with a HTTP 200 and refund_accepted message
    And the account holder balance shown for trenette-active-campaign is 0
    Then there is REWARD_UPDATE activity appeared

  @bpl-734-2 @bpl-734 @bpl
  Scenario: REWARD_UPDATE activity created when we process refund [slush>refund]
    Given an active account holder exists for the retailer
    When BPL receives a transaction for the account holder for the amount of 3333 pennies
    Then the account holder balance shown for trenette-active-campaign is 0
    And 2 pending rewards are available to the account holder for the trenette-active-campaign campaign
    When BPL receives a transaction for the account holder for the amount of -1200 pennies
    Then BPL responds with a HTTP 200 and refund_accepted message
    And the account holder balance shown for trenette-active-campaign is 0
    Then there is REWARD_UPDATE activity appeared
