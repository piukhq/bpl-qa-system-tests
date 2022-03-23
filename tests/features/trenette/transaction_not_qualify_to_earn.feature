# Created by rupalpatel at 23/03/2022
Feature: Bink BPL - Transaction doesn't meet threshold
  As a customer
  I am doing transaction with less then threshold amount
  So I make sure that I dont get balance increament

  @bpl @test
  Scenario: Transaction doesn’t qualify for earn
    Given the trenette retailer exists
    And that retailer has the trenette-stmp-campaign-1 campaign configured
    And required fetch type are configured for the current retailer
    And that campaign has the standard reward config configured with 1 allocable rewards
    And an active account holder exists for the retailer
    When BPL receives a transaction for the account holder for the amount of 480 pennies
    Then the account holder get a HTTP 200 with threshold_not_met response
