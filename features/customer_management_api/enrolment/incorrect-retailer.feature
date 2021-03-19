@bpl
Feature: Bink BPL - Ensure a customer can enrol the POST end point to authorise and call Customer management api system
  As a customer
  I want to utilise POST enrol endpoint
  So I can access to customer management system


  @bpl
  Scenario: Try to create an account holder for a non-existing retailer

    When I Enrol a incorrect-retailer User account passing in all required and all optional fields
    Then I receive a HTTP 403 status code in the response
    And I get a invalid_merchant response body
    And my user is not saved in the database
