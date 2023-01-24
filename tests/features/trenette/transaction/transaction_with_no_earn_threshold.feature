# Created by rupalpatel at 22/03/2022
Feature: Transaction with no earn threshold
  As a customer
  There is no earn threshold match set up
  So I make sure that balance get increase whatever I transact

  Background:
    Given the trenette retailer exists with status as TEST
    And the retailer has a REWARD_ISSUANCE email template configured with template id 99999999
    And the email template with template id 99999999 has the following required template variables: reward_url, account_number, first_name
    And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None
    And the retailer has a 10percentoff reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type

    And the retailer's trenette-acc-campaign-1 ACCUMULATOR campaign starts 5 days ago and ends in a day and is ACTIVE
    And the trenette-acc-campaign-1 campaign has an earn rule with a threshold of 0, an increment of 0, a multiplier of 1 and max amount of 0
    And the trenette-acc-campaign-1 campaign has reward rule with reward goal: 10000, allocation window: 0 and reward cap: 0

    And there is 2 rewards configured for the 10percentoff reward config, with account holder set to None and deleted status set to false

  @bpl @transaction @noearn-threshold
  Scenario Outline: Transaction with 0 threshold to verify balance and rewards
    Given an active account holder exists for the retailer
    When BPL receives a transaction for the account holder for the amount of <tx_amount_1> pennies
    Then the account holder balance shown for trenette-acc-campaign-1 is <expected_balance_1>
    And <expected_num_rewards_1> issued rewards are available to the account holder for the trenette-acc-campaign-1 campaign
    And the account holder balance shown for trenette-acc-campaign-1 is <expected_balance_1>
    When BPL receives a transaction for the account holder for the amount of <tx_amount_2> pennies
    Then the account holder balance shown for trenette-acc-campaign-1 is <expected_balance_2>
    And <expected_num_rewards_2> issued rewards are available to the account holder for the trenette-acc-campaign-1 campaign

    Examples:
      | tx_amount_1 | expected_balance_1 | tx_amount_2 | expected_balance_2 | expected_num_rewards_1 | expected_num_rewards_2 |
      | 2000        | 2000               | 650         | 2650               | 0                      | 0                      |
      | 2000        | 2000               | 8000        | 0                  | 0                      | 1                      |
      | 10000       | 0                  | 10000       | 0                  | 1                      | 2                      |
