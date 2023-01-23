# Created by rupalpatel at 20/10/2022
Feature: Reward code added via azure
  As a retailer
  I want to be able to provide new rewards for allocation when reward goals are met
  so that customers can be allocated rewards continuously

  Background:
    Given the trenette retailer exists with status as TEST
    And the retailer has a REWARD_ISSUANCE email template configured with template id 99999999
    And the email template with template id 99999999 has the following required template variables: reward_url, account_number, first_name
    And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None
    And the retailer has a 10percentoff reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type

    And the retailer's trenette-acc-campaign-1 ACCUMULATOR campaign starts 5 days ago and ends in a day and is ACTIVE
    And the trenette-acc-campaign-1 campaign has an earn rule with a threshold of 100, an increment of 0, a multiplier of 1 and max amount of 0
    And the trenette-acc-campaign-1 campaign has reward rule with reward goal: 700, allocation window: 0 and reward cap: 0

  @reward @bpl-678 @bpl-678-ac-1 @bpl
  Scenario: importing reward codes without expire date from azure blob storage
    Given the retailer provides 2 rewards in a csv file for the 10percentoff reward slug with rewards expiry date None
    Then the file is moved to the archive container by the reward importer
    And 2 reward codes available for reward slug 10percentoff with expiry date None in the rewards table

  @reward @bpl-678 @bpl-678-ac-2 @bpl
  Scenario: importing reward codes with expire date from azure blob storage
    Given the retailer provides 3 rewards in a csv file for the 10percentoff reward slug with rewards expiry date 2023-01-16
    Then the file is moved to the archive container by the reward importer
    And 3 reward codes available for reward slug 10percentoff with expiry date 2023-01-16 in the rewards table
