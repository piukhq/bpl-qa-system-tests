@bpl @cm @getbycredentials
Feature: Bink BPL - Ensure that as a channel user I can retrieve a test-retailer account holder details by credentials
  As a Channel User
  Using the POST /test-retailer/accounts/getbycredentials endpoint
  I can access the requested account holder details

  Scenario: Get an account holder for test-retailer by credentials

    Given I previously successfully enrolled a test-retailer account holder
    And I received a HTTP 202 status code response
    And the enrolled account holder has been activated
    When I post getbycredentials a test-retailer account holder passing in all required credentials
    Then I receive a HTTP 200 status code in the getbycredentials response
    And I get a success getbycredentials response body

  Scenario: Get a non existent account holder for test-retailer by credentials

    Given The test-retailer's account holder I want to retrieve does not exists
    When I post getbycredentials a test-retailer account holder passing in all required credentials
    Then I receive a HTTP 404 status code in the getbycredentials response
    And I get a no_account_found getbycredentials response body

  Scenario: POST getbycredentials request to retrieve an account holder with a malformed request

    When I getbycredentials a test-retailer account holder with an malformed request
    Then I receive a HTTP 400 status code in the getbycredentials response
    And I get a malformed_request getbycredentials response body

  Scenario: POST getbycredentials request to retrieve an account holder with a missing fields in the request

    When I getbycredentials a test-retailer account holder with a missing field in the request
    Then I receive a HTTP 422 status code in the getbycredentials response
    And I get a missing_fields getbycredentials response body

  Scenario: POST getbycredentials request to retrieve an account holder passing in fields that will fail validation in the request

    When I getbycredentials a test-retailer account holder passing in fields that will fail validation
    Then I receive a HTTP 422 status code in the getbycredentials response
    And I get a validation_failed getbycredentials response body
