@bpl @cm @enrol
Feature: Bink BPL - Ensure a customer can enrol the POST end point to authorise and call Customer management api system
  As a customer
  I want to utilise POST enrol endpoint
  So I can access to customer management system


  @bpl
  Scenario: Create a new account holder for test-retailer

    When I Enrol a test-retailer account holder passing in all required and all optional fields
    Then I receive a HTTP 202 status code in the response
    And I get a success enrol response body
    And all fields I sent in the enrol request are saved in the database

  @bpl
  Scenario: Create a new account holder for test-retailer omitting optional fields

    When I Enrol a test-retailer account holder passing in only required fields
    Then I receive a HTTP 202 status code in the response
    And I get a success enrol response body
    And all fields I sent in the enrol request are saved in the database

  @bpl
  Scenario: Try to create an existing account holder for test-retailer

    Given I previously enrolled a test-retailer account holder passing in all required and all optional fields
    And the previous response returned a HTTP 202 status code
    When I Enrol a test-retailer account holder passing in the same email as an existing account holder
    Then I receive a HTTP 409 status code in the response
    And I get a account_holder_already_exists enrol response body
