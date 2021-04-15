@bpl @getbycredentials
Feature: Bink BPL - Ensure that as a channel user I can not retrieve an account holder details by credentials via an invalid retailer
  As a Channel User
  Using the POST /test-retailer/accounts/getbycredentials endpoint
  I can not access the requested account holder details

  Scenario: POST getbycredentials request to retrieve an account holder for an invalid retailer

    When I post getbycredentials an invalid-retailer's account holder passing in all required credentials
    Then I receive a HTTP 403 status code in the getbycredentials response
    And I get a invalid_retailer getbycredentials response body

  Scenario: POST getbycredentials request to retrieve an account holder with an invalid authorisation token

    When I getbycredentials a incorrect-retailer account holder with an invalid authorisation token
    Then I receive a HTTP 401 status code in the getbycredentials response
    And I get a invalid_token getbycredentials response body
