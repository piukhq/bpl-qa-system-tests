@bpl @cm @accounts
Feature: Bink BPL - Ensure that as a channel user I can retrieve a test-retailer account holder details by UUID
  As a Channel User
  Using the GET /test-retailer/accounts/[AccountHolder.id] endpoint
  I can access the requested account holder details

  Scenario: Get an account holder for test-retailer by UUID

    Given I previously successfully enrolled a test-retailer account holder
    And I received a HTTP 202 status code response
    When I send a get /accounts request for a test-retailer account holder by UUID
    Then I receive a HTTP 200 status code in the accounts response
    And I get a success accounts response body

  Scenario: Get a non existent account holder for test-retailer by UUID

    Given The test-retailer's account holder I want to retrieve does not exists
    When I send a get /accounts request for a test-retailer account holder by UUID
    Then I receive a HTTP 404 status code in the accounts response
    And I get a no_account_found accounts response body

  Scenario: Get an account holder for test-retailer by UUID with a malformed UUID

    When I send a get /accounts request for a test-retailer account holder by UUID with a malformed UUID
    Then I receive a HTTP 404 status code in the accounts response
    And I get a no_account_found accounts response body

  Scenario: Get an account holder status for test-retailer by UUID

    Given I previously successfully enrolled a test-retailer account holder
    And I received a HTTP 202 status code response
    When I send a get /accounts request for a test-retailer account holder status by UUID
    Then I receive a HTTP 200 status code in the accounts response
    And I get a success accounts status response body

  Scenario: Get a non existent account holder status for test-retailer by UUID

    Given The test-retailer's account holder I want to retrieve does not exists
    When I send a get /accounts request for a test-retailer account holder status by UUID
    Then I receive a HTTP 404 status code in the accounts response
    And I get a no_account_found accounts response body

