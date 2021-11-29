@bpl @cm @accounts_status
Feature: Get a test-retailer account holder status
  As a reward rules management system
  Using the GET /test-retailer/accounts/[AccountHolder.id] endpoint
  I can access test-retailer account holder statuses


  Scenario: Get a test-retailer account holder status by UUID

    Given I previously successfully enrolled a test-retailer account holder
    And the previous response returned a HTTP 202 status code
    And the enrolled account holder has been activated
    When I send a get /accounts request for a test-retailer account holder status by UUID
    Then I receive a HTTP 200 status code response
    And I get a success accounts status response body

  
  Scenario: Get a non existent test-retailer account holder status by UUID

    Given The test-retailer account holder I want to retrieve does not exists
    When I send a get /accounts request for a test-retailer account holder status by UUID
    Then I receive a HTTP 404 status code response
    And I get a no_account_found accounts status response body
