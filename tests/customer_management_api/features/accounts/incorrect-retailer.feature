@bpl @cm @accounts
Feature: Bink BPL - Ensure that as a channel user I can not retrieve an account holder details by UUID via an invalid retailer
  As a Channel User
  Using the GET /test-retailer/accounts/[AccountHolder.id] endpoint
  I can not access the requested account holder details


  Scenario: GET accounts request to retrieve an account holder for an invalid retailer

    When I send a get /accounts request for an invalid-retailer account holder by UUID
    Then I receive a HTTP 403 status code response
    And I get a invalid_retailer accounts response body


  Scenario: GET accounts request to retrieve an account holder with an invalid authorisation token

    When I send a get /accounts request for a invalid-retailer account holder by UUID with an invalid authorisation token
    Then I receive a HTTP 401 status code response
    And I get a invalid_token accounts response body


  Scenario: GET accounts request to retrieve an account holder without a channel header

    When I send a get /accounts request for a invalid-retailer account holder by UUID without a channel header
    Then I receive a HTTP 400 status code response
    And I get a missing_channel_header accounts response body




