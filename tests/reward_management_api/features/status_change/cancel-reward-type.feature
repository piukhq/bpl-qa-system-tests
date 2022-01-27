@bpl @vm @rewardtypestatus
Feature: Cancel a reward type for a retailer
  As a system
  I want the Reward management system to be able to remove rewards for a cancelled/ended campaign
  using the PATCH /{retailer_slug}/rewards/{reward_slug}/status endpoint

  Scenario: Cancel reward type for retailer (happy path)

    Given there is an ACTIVE reward configuration for test-retailer with unallocated rewards
    When I perform a PATCH operation against the correct reward slug status endpoint instructing a cancelled status change
    Then I receive a HTTP 202 status code response
    And the status of the reward config is CANCELLED

  Scenario: End reward type for retailer (happy path)

    Given there is an ACTIVE reward configuration for test-retailer with unallocated rewards
    When I perform a PATCH operation against the correct reward slug status endpoint instructing a ended status change
    Then I receive a HTTP 202 status code response
    And the status of the reward config is ENDED

  Scenario: Cancel reward type for invalid retailer

    Given there are no reward configurations for invalid-test-retailer
    When I perform a PATCH operation against the incorrect reward slug status endpoint instructing a cancelled status change
    Then I receive a HTTP 403 status code response
    And  I get a invalid_retailer status response body

  Scenario: Cancel reward type for retailer (unknown reward_slug)

    Given there is an ACTIVE reward configuration for test-retailer with unallocated rewards
    When I perform a PATCH operation against the incorrect reward slug status endpoint instructing a cancelled status change
    Then I receive a HTTP 404 status code response
    And the status of the reward config is ACTIVE
    And I get a unknown_reward_type status response body

  Scenario: Cancel reward type for retailer (incorrect status transition)

    Given there is an CANCELLED reward configuration for test-retailer with unallocated rewards
    When I perform a PATCH operation against the correct reward slug status endpoint instructing a cancelled status change
    Then I receive a HTTP 409 status code response
    And the status of the reward config is CANCELLED
    And I get a update_failed status response body

  Scenario: Alter reward type for retailer (bad data)

    Given there is an ACTIVE reward configuration for test-retailer with unallocated rewards
    When I perform a PATCH operation against the correct reward slug status endpoint instructing a bad-status status change
    Then I receive a HTTP 422 status code response
    And the status of the reward config is ACTIVE
    And I get a failed_validation status response body


  Scenario: Cancel reward type for retailer with invalid token

    Given there is an ACTIVE reward configuration for test-retailer with unallocated rewards
    When I perform a PATCH operation with invalid token against the correct reward slug status endpoint instructing a cancelled status change
    Then I receive a HTTP 401 status code response
    And the status of the reward config is ACTIVE
    And I get a invalid_token status response body

