# Created by rupalpatel at 11/01/2022
Feature: Bink BPL - Transaction Activity
  As a customer
  I want to the enrol with retailer
  So that activity should appear

  @bpl-905-1 @accepted @bpl
  Scenario: Transaction activity - refund window
    Given the trenette retailer exists with status as TEST
    And the retailer has a WELCOME_EMAIL email template configured with template id 99999999
    And the email template with template id 99999999 has the following required template variables: first_name, last_name, account_number, marketing_token

    And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None
    And the retailer's trenette-active-campaign ACCUMULATOR campaign starts 10 days ago and ends in a day and is ACTIVE
    And the trenette-active-campaign campaign has an earn rule with a threshold of 500, an increment of 100, a multiplier of 1 and max amount of 0
    And the trenette-active-campaign campaign has reward rule with reward goal: 700, allocation window: 1 and reward cap: 0
    And the retailer has a 10percentoff reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type
    And there is 2 rewards configured for the 10percentoff reward config, with allocation status set to false and deleted status set to false

    And an active account holder exists for the retailer
    When BPL receives a transaction for the account holder for the amount of 750 pennies
    Then the account holder balance shown for trenette-active-campaign is 50
    And there is TX_IMPORT activity appeared
    And there is TX_HISTORY activity appeared
    And there is BALANCE_CHANGE activity appeared
    And there is REWARD_STATUS activity appeared
    When BPL receives a transaction for the account holder for the amount of -700 pennies
    Then the account holder balance shown for trenette-active-campaign is 50
    And there is REWARD_STATUS activity appeared
    And there is TX_IMPORT activity appeared
    And there is TX_HISTORY activity appeared
    When BPL receives a transaction for the account holder for the amount of -500 pennies
    Then there is REFUND_NOT_RECOUPED activity appeared
    And there is TX_IMPORT activity appeared
    And there is TX_HISTORY activity appeared
    And there is BALANCE_CHANGE activity appeared
    And there is REWARD_STATUS activity appeared

  @bpl-905-2 @accepted @bpl
  Scenario: Transaction activity - no refund window
    Given the trenette retailer exists with status as TEST
    And the retailer has a WELCOME_EMAIL email template configured with template id 99999999
    And the email template with template id 99999999 has the following required template variables: first_name, last_name, account_number, marketing_token

    And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None
    And the retailer's trenette-active-campaign ACCUMULATOR campaign starts 10 days ago and ends in a day and is ACTIVE
    And the trenette-active-campaign campaign has an earn rule with a threshold of 500, an increment of 100, a multiplier of 1 and max amount of 0
    And the trenette-active-campaign campaign has reward rule with reward goal: 700, allocation window: 0 and reward cap: 0
    And the retailer has a 10percentoff reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type
    And there is 2 rewards configured for the 10percentoff reward config, with allocation status set to false and deleted status set to false

    And an active account holder exists for the retailer
    When BPL receives a transaction for the account holder for the amount of 750 pennies
    Then there is BALANCE_CHANGE activity appeared
    And there is TX_IMPORT activity appeared
    And there is TX_HISTORY activity appeared
    And the account holder balance shown for trenette-active-campaign is 50
    And there is BALANCE_CHANGE activity appeared
    And there is REWARD_STATUS activity appeared
