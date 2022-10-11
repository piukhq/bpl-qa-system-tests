# Created by rupalpatel at 23/03/2022
Feature: Bink BPL - Transaction doesn't meet threshold
  As a customer
  I am doing transaction with less then threshold amount
  So I make sure that I dont get reward or balance increament

  @bpl @transaction @bpl-308
  Scenario Outline: Transaction doesn’t qualify for earn
    Given the trenette retailer exists
    And the retailer's <campaign_type> <loyalty_type> campaign starts 5 days ago and ends in a day and is ACTIVE
    And the <campaign_type> campaign has an earn rule with a threshold of 500, an increment of <increment>, a multiplier of 1 and max amount of <max_amount>
    And the <campaign_type> campaign has reward rule with reward goal: <reward_goal>, reward slug: <reward_slug>, allocation window: 0 and reward cap: 0
    And required fetch type are configured for the current retailer
    And that campaign has the standard reward config configured with 1 allocable rewards

    And an active account holder exists for the retailer
    When BPL receives a transaction for the account holder for the amount of 480 pennies
    Then BPL responds with a HTTP 200 and threshold_not_met message
    And the account holder balance shown for <campaign_type> is 0
    And 0 issued rewards are available to the account holder for the <campaign_type> campaign

    Examples:
      | campaign_type         | loyalty_type | increment | reward_goal | reward_slug     | max_amount |
      | trenette-acc-campaign | ACCUMULATOR  | 0         | 1000        | 20percent_egift | 0          |

  @bpl @transaction @bpl-308
  Scenario Outline: Account holder already has balance but new transaction doesn't qualify for earn and balance
    Given the trenette retailer exists
    And the retailer's <campaign_type> <loyalty_type> campaign starts 5 days ago and ends in a day and is ACTIVE
    And the <campaign_type> campaign has an earn rule with a threshold of 500, an increment of <increment>, a multiplier of 1 and max amount of 0
    And the <campaign_type> campaign has reward rule with reward goal: <reward_goal>, reward slug: <reward_slug>, allocation window: 0 and reward cap: 0
    And required fetch type are configured for the current retailer
    And that campaign has the standard reward config configured with 1 allocable rewards

    And an active account holder exists for the retailer
    When BPL receives a transaction for the account holder for the amount of <transaction_amount_1> pennies
    Then <expected_reward> issued rewards are available to the account holder for the <campaign_type> campaign
    And the account holder balance shown for <campaign_type> is <expected_balance>
    When BPL receives a transaction for the account holder for the amount of <transaction_amount_2> pennies
    Then BPL responds with a HTTP 200 and threshold_not_met message
    And the account holder balance shown for <campaign_type> is <expected_balance>
    And <expected_reward> issued rewards are available to the account holder for the <campaign_type> campaign

    Examples:
      | campaign_type          | transaction_amount_1 | transaction_amount_2 | expected_balance | expected_reward | loyalty_type | increment | reward_goal | reward_slug |
      | trenette-stmp-campaign | 770                  | 480                  | 100              | 0               | STAMPS       | 100       | 700         | free-item   |


