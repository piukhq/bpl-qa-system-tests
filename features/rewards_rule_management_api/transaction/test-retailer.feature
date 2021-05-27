@bpl @rrm @transaction
Feature: Post a transaction for a test-retailer
  As a transaction matching system
  Using the POST /test-retailer/transaction endpoint
  I can store a transaction in the RRM database
  @test
  Scenario: Successfully POST a transaction

    Given A active account holder exists
    When I send a POST transaction request with the correct payload for a test-retailer with the correct token
    Then I get a HTTP 200 rrm response
    And The transaction is saved in the database

  Scenario: Send a POST transaction request with the wrong payload

    When I send a POST transaction request with the incorrect payload for a test-retailer with the correct token
    Then I get a HTTP 422 rrm response
    And The transaction is not saved in the database

  Scenario: Send a POST transaction request for a inactive account holder

    Given A inactive account holder exists
    When I send a POST transaction request with the correct payload for a test-retailer with the correct token
    Then I get a HTTP 409 rrm response
    And The transaction is not saved in the database

  Scenario: Send a POST transaction request for a non existent account holder

    Given An account holder does not exists
    When I send a POST transaction request with the correct payload for a test-retailer with the correct token
    Then I get a HTTP 404 rrm response
    And The transaction is not saved in the database

