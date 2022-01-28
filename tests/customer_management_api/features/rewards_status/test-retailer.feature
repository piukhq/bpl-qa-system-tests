@bpl @cm @rewardstatus
Feature: Bink BPL - Ensure that as a bpl service I can update an account holder's reward status
  As a bpl service
  Using the PATCH /test-retailer/rewards/{reward_uuid}/status endpoint
  I can update the requested reward status


  Scenario: Update a reward's status to redeemed
    Given A active account holder exists for test-retailer
    And The account holder has an issued reward
    When I PATCH a reward's status to redeemed for a test-retailer using a valid auth token
    Then I receive a HTTP 200 status code in the rewards status response
    And I get a success reward status response body
    And The account holders will have the reward's status updated in their account


  Scenario: Update a reward's status to cancelled
    Given A active account holder exists for test-retailer
    And The account holder has an issued reward
    When I PATCH a reward's status to cancelled for a test-retailer using a valid auth token
    Then I receive a HTTP 200 status code in the rewards status response
    And I get a success reward status response body
    And The account holders will have the reward's status updated in their account


  Scenario: Update a non issued reward's status
    Given A active account holder exists for test-retailer
    And The account holder has an non issued reward
    When I PATCH a reward's status to redeemed for a test-retailer using a valid auth token
    Then I receive a HTTP 202 status code in the rewards status response
    And I get a status_not_changed reward status response body


  Scenario: Update a reward's status to a non supported value
    Given A active account holder exists for test-retailer
    And The account holder has an issued reward
    When I PATCH a reward's status to a-wrong-value for a test-retailer using a valid auth token
    Then I receive a HTTP 400 status code in the rewards status response
    And I get a invalid_status reward status response body
    And The account holders will not have the reward's status updated in their account


  Scenario: Update a non existing reward's status
    Given There is no reward to update
    When I PATCH a reward's status to redeemed for a test-retailer using a valid auth token
    Then I receive a HTTP 404 status code in the rewards status response
    And I get a no_reward_found reward status response body
