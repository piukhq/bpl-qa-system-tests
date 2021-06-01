@bpl @rrm @transaction
Feature: Post a transaction for a test-retailer
  As a transaction matching system
  Using the POST /test-retailer/transaction endpoint
  I can store a transaction in the RRM database

  Scenario: Successfully POST a transaction

    Given A active account holder exists for test-retailer
    When I send a POST transaction request with the correct payload for a test-retailer with the correct token
    Then I get a HTTP 200 rrm success response
    And The transaction is saved in the database

  Scenario: Send a POST transaction request for an existing transaction

    Given A active account holder exists for test-retailer
    And A POST transaction with the correct payload for a test-retailer with the correct token was already sent
    When I send a POST transaction request with the correct payload for a test-retailer with the correct token
    Then I get a HTTP 409 rrm duplicate_transaction response

  Scenario: Send a POST transaction request with the wrong payload

    When I send a POST transaction request with the incorrect payload for a test-retailer with the correct token
    Then I get a HTTP 422 rrm invalid_content response
    And The transaction is not saved in the database

  Scenario: Send a POST transaction request for a inactive account holder

    Given A inactive account holder exists for test-retailer
    When I send a POST transaction request with the correct payload for a test-retailer with the correct token
    Then I get a HTTP 409 rrm user_not_active response
    And The transaction is not saved in the database

  Scenario: Send a POST transaction request for a non existent account holder

    Given An account holder does not exists for test-retailer
    When I send a POST transaction request with the correct payload for a test-retailer with the correct token
    Then I get a HTTP 404 rrm user_not_found response
    And The transaction is not saved in the database
