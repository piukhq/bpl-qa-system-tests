Feature: Bink BPL - Jigshaw egift - End campaign and delete/issue pending rewards
  As a retailer
  I am ending the campaign
  So I make sure all pending rewards gets deleted/issued too

  Background:
    Given the asos retailer exists
    And the retailer has a REWARD_ISSUANCE email template configured with template id 99999999
    And the email template with template id 99999999 has the following required template variables: reward_url, account_number, first_name
    And the retailer's new-campaign ACCUMULATOR campaign starts 5 days ago and ends in a day and is ACTIVE
    And the retailer's old-campaign ACCUMULATOR campaign starts 5 days ago and ends in a day and is ACTIVE
    And a JIGSAW_EGIFT fetch type is configured for the current retailer with an agent config brand id 30
    And the retailer has a old-campaign reward config configured with transaction_value: 100, and a status of ACTIVE and a JIGSAW_EGIFT fetch type
    And the retailer has a new-campaign reward config configured with transaction_value: 100, and a status of ACTIVE and a JIGSAW_EGIFT fetch type
    And the old-campaign campaign has an earn rule with a threshold of 0, an increment of 100, a multiplier of 1 and max amount of 0
    And the old-campaign campaign has reward rule of 10000, with reward slug old-campaign and allocation window 1
    And the new-campaign campaign has an earn rule with a threshold of 0, an increment of 100, a multiplier of 1 and max amount of 0
    And the new-campaign campaign has reward rule of 10000, with reward slug new-campaign and allocation window 1
    And the retailer has 5 active account holders
    And the account holders each have 2 ISSUED rewards with the old-campaign reward slug expiring in 5 days
    And the account holders each have 2 ISSUED rewards with the new-campaign reward slug expiring in 5 days
    And the account holders each have 2 pending rewards for the old-campaign campaign and old-campaign reward slug with a value of 10000
    And the account holders each have 2 pending rewards for the new-campaign campaign and new-campaign reward slug with a value of 10000
    And there is 2 rewards configured for the old-campaign reward config, with allocation status set to false and deleted status set to false
    And there is 2 rewards configured for the new-campaign reward config, with allocation status set to false and deleted status set to false


  @bpl @asos @bpl-517 @bpl-516
  Scenario Outline: End campaign - delete/issue the pending rewards
    When the retailer's old-campaign campaign status is changed to ended with pending rewards to be <issued_deleted>
    And the old-campaign reward config status has been updated to ENDED
    And each account holder has a queued reward-adjustment task for the old-campaign campaign with an adjustment amount of 100
    And each account holder has a queued reward-adjustment task for the new-campaign campaign with an adjustment amount of 100
    And there are reward-issuance tasks for the account holders for the old-campaign reward slug on the queue
    And there are reward-issuance tasks for the account holders for the new-campaign reward slug on the queue
    Then there are 2 rewards for the old-campaign reward config, with allocated set to false and deleted set to false
    And there are 2 rewards for the new-campaign reward config, with allocated set to false and deleted set to false
    And queued reward-adjustment tasks for the account holders for the old-campaign campaign are in status of CANCELLED
    And queued reward-adjustment tasks for the account holders for the new-campaign campaign are in status of SUCCESS
    And queued reward-issuance tasks for the account holders for the old-campaign reward are in status of SUCCESS
    And queued reward-issuance tasks for the account holders for the new-campaign reward are in status of SUCCESS
    And <num_pending_rewards> pending rewards are available to each account holder
    And <num_issued_rewards> issued rewards are available to each account holder
    And the balance shown for each account holder for the new-campaign campaign is 1
    And no balance is shown for each account holder for the old-campaign campaign

    Examples:
      | issued_deleted | num_pending_rewards | num_issued_rewards |
      | deleted        | 2                   | 6                  |
      | issued         | 2                   | 8                  |