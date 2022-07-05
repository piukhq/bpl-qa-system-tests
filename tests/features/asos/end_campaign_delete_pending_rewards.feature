Feature: Bink BPL - Jigshaw egift - End campaign and delete pending rewards
  As a retailer
  I am ending the campaign
  So I make sure all pending rewards gets deleted too

  Background:
    Given the asos retailer exists
    And the retailer's asos-campaign ACCUMULATOR campaign starts 5 days ago and ends in a day and is ACTIVE
    And the asos-campaign campaign has an earn rule with a threshold of 0, an increment of 100, a multiplier of 1 and max amount of 0
    And the asos-campaign campaign has reward rule of 10000, with reward slug free-item and allocation window 1
    And a JIGSAW_EGIFT fetch type is configured for the current retailer with an agent config brand id 30
    And the retailer has a free-item reward config configured with transaction_value: 10, and a status of ACTIVE and a JIGSAW_EGIFT fetch type
    And there is 2 reward configured for the free-item reward config, with allocation status set to false and deleted status set to false


    And the retailer's asos-draft-campaign ACCUMULATOR campaign starts 5 days ago and ends in a week and is DRAFT
    And the asos-draft-campaign campaign has an earn rule with a threshold of 1000, an increment of 200 and a multiplier of 1
    And the asos-draft-campaign campaign has reward rule of 900, with reward slug 10percentoff and allocation window 1
    And the retailer has a 10percentoff reward config configured with validity_days: 30, and a status of ACTIVE and a JIGSAW_EGIFT fetch type
    And there is 2 reward configured for the 10percentoff reward config, with allocation status set to false and deleted status set to false

  @bpl @asos @bpl-517
  Scenario: End campaign - delete the pending rewards
    Given an active account holder exists for the retailer
    And the account has 3 issued unexpired rewards
    When BPL receives a transaction for the account holder for the amount of 15000 pennies
    Then the account holder's asos-campaign balance is returned as 5000
    And 1 pending rewards are available to the account holder

    And the retailer's asos-draft-campaign campaign status is changed to active
    And the retailer's requested asos-campaign to ended the campaign and delete pending rewards
    And all unallocated rewards for free-item reward config are soft deleted

    And 0 pending rewards are available to the account holder

    Then any pending rewards for asos-campaign are deleted
    And the account holder's asos-campaign balance no longer exists

    And 3 issued rewards are available to the account holder

    And the polaris delete-campaign-balances task status is success
    And the polaris delete-pending-rewards task status is success

    When the vela convert-or-delete-pending-rewards task status is success
    And the vela reward-status-adjustment task status is success
    And the vela delete-campaign-balances task status is success

    Then the carina delete-unallocated-rewards task status is success



