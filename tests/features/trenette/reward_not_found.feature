# Created by rupalpatel at 29/04/2022
Feature: Reward already allocated and uploading status from 3rd party
  As a retailer
  I want to be able to provide a rewards for allocation which are already allocated
  so that customers can not use reward

  Background:
    Given the trenette retailer exists
    And the retailer's trenette-acc-campaign-1 ACCUMULATOR campaign starts 5 days ago and ends in a day and is ACTIVE
    And the trenette-acc-campaign-1 campaign has an earn rule with a threshold of 100, an increment of 0, a multiplier of 1 and max amount of 0
    And the trenette-acc-campaign-1 campaign has reward rule of 700, with reward slug 10percentoff and allocation window 0
    And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None
    And the retailer has a 10percentoff reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type
    And there is 2 rewards configured for the 10percentoff reward config, with allocation status set to true and deleted status set to false

  @reward @bpl @bpl_299
  Scenario: Reward allocated in carina not found in polaris
    Given an account holder reward with this reward uuid does not exist
    When the trenette retailer updates selected rewards to redeemed status
    Then the imported rewards are soft deleted
