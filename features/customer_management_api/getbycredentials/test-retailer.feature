@bpl
Feature: Bink BPL - Ensure that as a channel user I can retrieve a test-retailer account holder details by credentials
  As a Channel User
  Using the POST /test-retailer/accounts/getbycredentials endpoint
  I can access the requested account holder details

  @bpl @noice
  Scenario: Get an account holder for test-retailer by credentials

    Given I previously enrolled a test-retailer account holder passing in all required and all optional fields
    And the previous response returned a HTTP 202 status code
    When I post getbycredentials a test-retailer account holder passing in all required credentials
    Then I receive a HTTP 200 status code in the response
    And I get a success getbycredentials response body
