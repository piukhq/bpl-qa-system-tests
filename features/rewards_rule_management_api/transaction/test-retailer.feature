@bpl @rrm @transaction
Feature: Post a transaction for a test-retailer
  As a transaction matching system
  Using the POST /test-retailer/transaction endpoint
  I can store a transaction in the RRM database

  Scenario: Successfully POST an awardable transaction

    Given A active account holder exists for test-retailer
    When I send a POST transaction request with the over the threshold payload for a test-retailer with the correct token
    Then I get a HTTP 200 rrm awarded response
    And The transaction is not saved in the transaction database table
    And The transaction is saved in the processed_transaction database table
    And The account holder's balance is updated

  Scenario: Successfully POST a non awardable transaction

    Given A active account holder exists for test-retailer
    When I send a POST transaction request with the under the threshold payload for a test-retailer with the correct token
    Then I get a HTTP 200 rrm threshold_not_met response
    And The transaction is not saved in the transaction database table
    And The transaction is saved in the processed_transaction database table

  Scenario: Send a POST transaction request for an existing transaction

    Given A active account holder exists for test-retailer
    And A POST transaction with the over the threshold payload for a test-retailer with the correct token was already sent
    When I send a POST transaction request with the over the threshold payload for a test-retailer with the correct token
    Then I get a HTTP 409 rrm duplicate_transaction response

  Scenario: Send a POST transaction request with the wrong payload

    When I send a POST transaction request with the incorrect payload for a test-retailer with the correct token
    Then I get a HTTP 422 rrm invalid_content response
    And The transaction is not saved in the transaction database table

  Scenario: Send a POST transaction request for a inactive account holder

    Given A inactive account holder exists for test-retailer
    When I send a POST transaction request with the over the threshold payload for a test-retailer with the correct token
    Then I get a HTTP 409 rrm user_not_active response
    And The transaction is not saved in the transaction database table

  Scenario: Send a POST transaction request for a non existent account holder

    Given An account holder does not exists for test-retailer
    When I send a POST transaction request with the over the threshold payload for a test-retailer with the correct token
    Then I get a HTTP 404 rrm user_not_found response
    And The transaction is not saved in the transaction database table

  Scenario: Send a POST transaction request for a test-retailer dated too early to match any active campaigns

    Given A active account holder exists for test-retailer
    When I send a POST transaction request with the too early for active campaign payload for a test-retailer with the correct token
    Then I get a HTTP 404 rrm no_active_campaigns response
    And The transaction is saved in the transaction database table
    And The transaction is not saved in the processed_transaction database table
