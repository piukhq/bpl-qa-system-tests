Feature: Reward code status updated to cancelled from 3rd party
  As a retailer
  I want to be able to provide new rewards for cancelled
  so that customers can get cancelled rewards in their account

  Background:
    Given the trenette retailer exists with status as TEST
    And the retailer has a REWARD_ISSUANCE email template configured with template id 99999999
    And the email template with template id 99999999 has the following required template variables: reward_url, account_number, first_name
    And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None
    And the retailer has a 10percentoff reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type

    And the retailer's trenette-acc-campaign-1 ACCUMULATOR campaign starts 5 days ago and ends in a day and is ACTIVE
    And the trenette-acc-campaign-1 campaign has an earn rule with a threshold of 100, an increment of 0, a multiplier of 1 and max amount of 0
    And the trenette-acc-campaign-1 campaign has reward rule with reward goal: 700, allocation window: 0 and reward cap: 0

    And 1 unassigned rewards are generated for the 10percentoff reward config with deleted status set to false

  @reward @bpl @bpl-300
  Scenario: Handle importing cancelled reward codes from a 3rd party
    Given an active account holder exists for the retailer
    When BPL receives a transaction for the account holder for the amount of 701 pennies
    Then the account holder balance shown for trenette-acc-campaign-1 is 1
    And 1 issued rewards are available to the account holder for the trenette-acc-campaign-1 campaign
    When the trenette retailer updates selected rewards to cancelled status
    Then the file is moved to the archive container by the reward importer
    And the status of the allocated account holder for trenette rewards are updated with CANCELLED
    And 1 reward for the account holder shows as cancelled with redeemed date
