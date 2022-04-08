# Created by rupalpatel at 05/04/2022
Feature: Reward code status updated from 3rd party
  As a retailer
  I want to be able to provide new rewards for allocation when reward goals are met
  so that customers can be allocated rewards continuously

  Background:
    Given the trenette retailer exists
    And the retailer's trenette-acc-campaign-1 ACCUMULATOR campaign starts 5 days ago and ends in a day and is ACTIVE
    And the trenette-acc-campaign-1 campaign has an ACCUMULATOR earn rule with a threshold of 100, an increment of 0 and a multiplier of 1
    And the trenette-acc-campaign-1 campaign has reward rule of 700, with reward slug 10percentoff and allocation window 0
    And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None
    And the retailer has a 10percentoff reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type
    And there is 1 reward configured for the 10percentoff reward config, with allocation status set to false and deleted status set to false

  @transaction @bpl @bpl_301 @davetest
  Scenario: Handle importing new reward codes from a 3rd party
    #To run these scenario we have to scale the carina cron worker with:
      # kubectl scale --replicas=0 deployment carina-cron-scheduler
      # restart the .scheduler file and run the test
    Given an active account holder exists for the retailer
    When BPL receives a transaction for the account holder for the amount of 701 pennies
    Then the account holder's trenette-acc-campaign-1 accumulator campaign balance 1 is updated
    And 1 rewards are available to the account holder
    When the file for trenette with redeemed status is imported
    Then the status of the allocated account holder for trenette rewards are updated with REDEEMED
    And 1 reward for the account holder shows as redeemed with redeemed date
