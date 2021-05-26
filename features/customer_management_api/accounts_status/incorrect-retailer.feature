@bpl @cm @accounts
Feature: Get an account holder status using an invalid retailer
  As a reward rules management system
  Using the GET /test-retailer/accounts/[AccountHolder.id]/status endpoint
  I can't get account holder statuses using an invalid retailer

  Scenario: Get an account holder status using an invalid retailer

    When I send a get /accounts request for an invalid-retailer account holder status by UUID
    Then I receive a HTTP 403 status code in the accounts response
    And I get a invalid_retailer accounts response body

  Scenario: Get an account holder status using an invalid retailer and invalid authorisation token

    When I send a get /accounts request for a invalid-retailer account holder status by UUID with an invalid authorisation token
    Then I receive a HTTP 401 status code in the accounts response
    And I get a invalid_token accounts response body
