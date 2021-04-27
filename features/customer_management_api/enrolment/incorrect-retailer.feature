@bpl @enrol
Feature: Bink BPL - Ensure a customer can enrol the POST end point to authorise and call Customer management api system
  As a customer
  I want to utilise POST enrol endpoint
  So I can access to customer management system


  @bpl
  Scenario: Try to create an account holder for a non-existing retailer

    When I Enrol a incorrect-retailer account holder passing in all required and all optional fields
    Then I receive a HTTP 403 status code in the response
    And I get a invalid_retailer enrol response body
    And the account holder is not saved in the database

  @bpl
  Scenario: POST Enrol request to create an account holder with a with an malformed request

    When I Enrol a test-retailer account holder with an malformed request
    Then I receive a HTTP 400 status code in the response
    And I get a malformed_request enrol response body


  @bpl
  Scenario: POST Enrol request to create an account holder with a with an missing fields in request

    Given I Enrol a test-retailer account holder with an missing fields in request
    Then I receive a HTTP 422 status code in the response
    And I get a missing_fields enrol response body
    And the account holder is not saved in the database


  @bpl
  Scenario: POST Enrol request to create an account holder passing in fields that will fail validation in the request

    Given I Enrol a test-retailer account holder and passing in fields will fail validation request
    Then I receive a HTTP 422 status code in the response
    And I get a validation_failed enrol response body
    And the account holder is not saved in the database


  @bpl
  Scenario: POST Enrol request to create an account holder with a with an invalid token

    Given I Enrol a test-retailer account holder with an invalid token
    Then I receive a HTTP 401 status code in the response
    And I get a invalid_token enrol response body
    And the account holder is not saved in the database

  @bpl
  Scenario: POST request without a channel HTTP header

    Given I POST a test-retailer account holder enrol request without a channel HTTP header
    Then I receive a HTTP 400 status code in the response
    And I get a missing_channel_header enrol response body
    And the account holder is not saved in the database


