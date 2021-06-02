@bpl @rrm @transaction
Feature: Post a transaction for an invalid retailer
  As a transaction matching system
  Using the POST /WRONG-RETAILER/transaction endpoint
  I can't store a transaction in the RRM database


  Scenario: Send a POST transaction request for an invalid retailer

    When I send a POST transaction request with the correct payload for a incorrect-retailer with the correct token
    Then I get a HTTP 403 rrm invalid_retailer response
    And The transaction is not saved in the database

  Scenario: Send a POST transaction request for an invalid retailer and with an invalid authorisation token

    When I send a POST transaction request with the correct payload for a incorrect-retailer with the incorrect token
    Then I get a HTTP 401 rrm invalid_token response
    And The transaction is not saved in the database
