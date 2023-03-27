# Created by rupalpatel at 09/06/2022
Feature: Bink BPL - Transaction exceeds earn rule max amount
  As a customer
  I want to transact some amount but reach to maximum earn rule amount
  So I make sure that my balance increase as per earn rule amount

  Background:
    Given the trenette retailer exists with status as TEST
    And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None
    And the retailer has a free-item reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type
    And the retailer has a REWARD_ISSUANCE email template configured with template id 99999999
    And the email template with template id 99999999 has the following required template variables: reward_url, account_number, first_name

    And the retailer's trenette-acc-campaign ACCUMULATOR campaign starts 5 days ago and ends in a day and is ACTIVE
    And the trenette-acc-campaign campaign has an earn rule with a threshold of 0, an increment of 100, a multiplier of 1 and max amount of 1000
    And the trenette-acc-campaign campaign has reward rule with reward goal: 10000, allocation window: None and reward cap: None

    And 1 unassigned rewards are generated for the free-item reward config with deleted status set to false

  @bpl @transaction @bpl-562 @bpl-2.0
  Scenario: Transaction exceeds earn rule max - Accumulator
    Given an active account holder exists for the retailer
    And the account holder's trenette-acc-campaign balance is 2000
    Then the account holder balance shown for trenette-acc-campaign is 2000
    When BPL receives a transaction for the account holder for the amount of 1250 pennies
    Then the account holder balance shown for trenette-acc-campaign is 3000
    And 0 issued rewards are available to the account holder for the trenette-acc-campaign campaign