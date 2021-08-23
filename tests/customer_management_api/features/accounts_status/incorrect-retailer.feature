@bpl @cm @accounts_status
Feature: Get an account holder status using an invalid retailer
  As a reward rules management system
  Using the GET /test-retailer/accounts/[AccountHolder.id]/status endpoint
  I can't get account holder statuses using an invalid retailer


  Scenario: Get an account holder status using an invalid retailer
    Given The invalid-retailer account holder I want to retrieve does not exists
    When I send a get /accounts request for a invalid-retailer account holder status by UUID
    Then I receive a HTTP 403 status code response
    And I get a invalid_retailer accounts status response body


  Scenario: Get an account holder status using an invalid retailer and invalid authorisation token

    When I send a get /accounts request for a invalid-retailer account holder status by UUID with an invalid authorisation token
    Then I receive a HTTP 401 status code response
    And I get a invalid_token accounts status response body
