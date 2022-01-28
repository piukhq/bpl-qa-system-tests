@bpl @cm @rewardstatus
Feature: Bink BPL - Ensure that as a bpl service I can't update an account holder's reward status using a incorrect-retailer
  As a bpl service
  Using the PATCH /test-retailer/reward/{reward_uuid}/status endpoint
  I can't update the requested reward status using a incorrect-retailer


  Scenario: Update a reward's status to redeemed for a incorrect-retailer
    Given A active account holder exists for test-retailer
    And The account holder has an issued reward
    When I PATCH a reward's status to redeemed for a incorrect-retailer using a valid auth token
    Then I receive a HTTP 403 status code in the rewards status response
    And I get a invalid_retailer reward status response body


  Scenario: Update a reward's status to redeemed for a incorrect-retailer with an invalid token
    Given A active account holder exists for test-retailer
    And The account holder has an issued reward
    When I PATCH a reward's status to redeemed for a incorrect-retailer using a invalid auth token
    Then I receive a HTTP 401 status code in the rewards status response
    And I get a invalid_token reward status response body
