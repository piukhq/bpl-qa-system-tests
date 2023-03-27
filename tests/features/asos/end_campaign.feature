Feature: Bink BPL - Jigshaw egift - End campaign and delete/issue pending rewards
  As a retailer
  I am ending the campaign
  So I make sure all pending rewards gets deleted/issued too

  Background:
    Given the trenette retailer exists with status as TEST
    And the retailer has a REWARD_ISSUANCE email template configured with template id 99999999
    And the email template with template id 99999999 has the following required template variables: reward_url, account_number, first_name
    And a JIGSAW_EGIFT fetch type is configured for the current retailer with an agent config brand id 30

    And the retailer has a old-campaign reward config configured with transaction_value: 100, and a status of ACTIVE and a JIGSAW_EGIFT fetch type
    And the retailer has a new-campaign reward config configured with transaction_value: 100, and a status of ACTIVE and a JIGSAW_EGIFT fetch type

    And the retailer's new-campaign ACCUMULATOR campaign starts 5 days ago and ends in a day and is ACTIVE
    And the retailer's old-campaign ACCUMULATOR campaign starts 5 days ago and ends in a day and is ACTIVE

    And the old-campaign campaign has an earn rule with a threshold of 0, an increment of 100, a multiplier of 1 and max amount of 0
    And the old-campaign campaign has reward rule with reward goal: 10000, allocation window: 1 and reward cap: None

    And the new-campaign campaign has an earn rule with a threshold of 0, an increment of 100, a multiplier of 1 and max amount of 0
    And the new-campaign campaign has reward rule with reward goal: 10000, allocation window: 1 and reward cap: None


    And the retailer has 5 active account holders
    And the account holders each have 2 ISSUED rewards for the old-campaign campaign with the old-campaign reward slug expiring in 5 days
    And the account holders each have 2 ISSUED rewards for the new-campaign campaign with the new-campaign reward slug expiring in 5 days
    And the account holders each have 2 pending rewards for the old-campaign campaign and old-campaign reward slug with a value of 10000
    And the account holders each have 2 pending rewards for the new-campaign campaign and new-campaign reward slug with a value of 10000

  @bpl @asos @bpl-517 @bpl-516 @bpl-2.0
  Scenario Outline: End campaign - delete/issue the pending rewards
    When the retailer's old-campaign campaign is ended with pending rewards to be <issued_deleted>
    And there are reward-issuance tasks for the account holders for the old-campaign reward slug and old-campaign campaign_slug on the queue
    And there are reward-issuance tasks for the account holders for the new-campaign reward slug and new-campaign campaign_slug on the queue
    Given 2 unassigned rewards are generated for the old-campaign reward config with deleted status set to false
    And 2 unassigned rewards are generated for the new-campaign reward config with deleted status set to false
    Then queued reward-issuance tasks for the account holders for the old-campaign reward are in status of SUCCESS
    And queued reward-issuance tasks for the account holders for the new-campaign reward are in status of SUCCESS
    And <num_pending_rewards> pending rewards are available to each account holder for the new-campaign campaign
    And <num_issued_rewards_new_campaign> issued rewards are available to each account holder for the new-campaign campaign
    And <num_issued_rewards_old_campaign> issued rewards are available to each account holder for the old-campaign campaign
    And the balance shown for each account holder for the new-campaign campaign is 0
    And no balance is shown for each account holder for the old-campaign campaign

    Examples:
      | issued_deleted | num_pending_rewards | num_issued_rewards_new_campaign | num_issued_rewards_old_campaign |
      | deleted        | 2                   | 3                               | 3                               |
      | issued         | 2                   | 3                               | 3                               |