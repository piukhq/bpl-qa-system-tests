@bpl
Feature: Bink BPL - Ensure a customer can enrol the POST end point to authorise and call Customer management api system
  As a customer
  I want to utilise POST enrol endpoint
  So I can access to customer management system


  @bpl
  Scenario: Create a BPL user account

    When I Enrol a test-retailer User account passing in all required and all optional fields
    Then I receive a 202 HTTP status code back with an empty response body
    And All fields I sent in the enrol request are saved in the database
