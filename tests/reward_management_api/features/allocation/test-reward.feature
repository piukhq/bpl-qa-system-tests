@bpl @vm
Feature: Allocate a specific reward type to an account
  As a system
  I want the Reward management system to be able to send and receive requests and responses
  from other BPL internal systems so that a customer can be issued a reward and their Account updated.
  Using the POST /{retailer_slug}/rewards/{reward_slug}/allocation endpoint


  Scenario: Allocate a specific reward type to an account for test-retailer with a valid reward_slug

    Given A active account holder exists for test-retailer
    And there are at least 1 reward configs for test-retailer
    And there are rewards that can be allocated for the existing reward configs
    When I perform a POST operation against the allocation endpoint for a test-retailer account holder with a valid auth token
    Then I receive a HTTP 202 status code response
    And a Reward code will be allocated asynchronously
    And the expiry date is calculated using the expiry window for the reward_slug from the Reward Management Config
    And a POST to /rewards will be made to update the users account with the reward allocation


  Scenario:  Allocate a specific reward type to an account for test-retailer with an invalid reward_slug

    Given A active account holder exists for test-retailer
    And there are at least 1 reward configs for test-retailer
    And there are rewards that can be allocated for the existing reward configs
    When I perform a POST operation against the allocation endpoint for a test-retailer account holder with a invalid auth token
    Then I receive a HTTP 401 status code response
    And I get a invalid_token reward allocation response body
