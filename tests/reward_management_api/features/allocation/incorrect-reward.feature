@bpl @vm
Feature: Allocate a specific reward type to an account
  As a system
  I want the Reward management system to be able to send and receive requests and responses
  from other BPL internal systems so that a customer can be issued a reward and their Account updated.
  Using the POST /{retailer_slug}/rewards/{reward_slug}/allocation endpoint


  Scenario: Allocate a specific reward type to an account for test-retailer with a malformed request

    Given A active account holder exists for test-retailer
    And there are at least 1 reward configs for test-retailer
    And there are rewards that can be allocated for the existing reward configs
    When I perform a POST operation against the allocation endpoint for a test-retailer account holder with a malformed request
    Then I receive a HTTP 400 status code response
    And I get a malformed_request reward allocation response body


  Scenario: Allocate a specific reward type to an account for test-retailer with a reward_slug that does not exist in the rewards table

    Given A active account holder exists for test-retailer
    And there are at least 1 reward configs for test-retailer
    And there are rewards that can be allocated for the existing reward configs
    When I allocate a specific reward type to an account for test-retailer with a reward_slug that does not exist in the reward table
    Then I receive a HTTP 404 status code response
    And I get a unknown_reward_slug reward allocation response body


  Scenario: Allocate a specific reward type to an account where the retailer slug supplied does not exist

    Given A active account holder exists for test-retailer
    And there are at least 1 reward configs for test-retailer
    And there are rewards that can be allocated for the existing reward configs
    When I perform a POST operation against the allocation endpoint for an account holder with a non-existent retailer
    Then I receive a HTTP 403 status code response
    And I get a invalid_retailer reward allocation response body
