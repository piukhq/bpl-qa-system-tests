@bpl @cm @rewards
Feature: Post a reward for a test-retailer
  As a VM system
  Using the POST [retailer_slug]/accounts/[account_holder_uuid]/rewards endpoint
  I can add an account holder reward


  Scenario: Successfully POST a reward

    Given I previously successfully enrolled a test-retailer account holder
    And the previous response returned a HTTP 202 status code
    And the enrolled account holder has been activated
    And I POST a reward expiring in the future for a test-retailer account holder with a valid auth token
    Then I receive a HTTP 200 status code response
    When I send a get /accounts request for the account holder by UUID
    Then the returned reward's status is issued and the reward data is well formed


  Scenario: Reward status is EXPIRED when expiry_date is in the past

    Given I previously successfully enrolled a test-retailer account holder
    And the previous response returned a HTTP 202 status code
    And the enrolled account holder has been activated
    And I POST a reward expiring in the past for a test-retailer account holder with a valid auth token
    Then I receive a HTTP 200 status code response
    When I send a get /accounts request for the account holder by UUID
    Then the returned reward's status is expired and the reward data is well formed
