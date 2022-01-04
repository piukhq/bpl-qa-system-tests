@bpl @cm @adjustments
Feature: Post a balance adjustment for a test-retailer
  As a RRM system
  Using the POST [retailer_slug]/accounts/[account_holder_uuid]/adjustments endpoint
  I can adjust an account holder balance


  Scenario: Successfully POST a balance adjustment

    Given I previously successfully enrolled a test-retailer account holder
    And the previous response returned a HTTP 202 status code
    And the enrolled account holder has been activated and i know its current balances
    When I post the balance adjustment for a test-retailer account holder with a valid auth token
    Then I receive a HTTP 200 status code response
    And The account holder's balance is updated in the database


  Scenario: POST a balance adjustment twice

    Given I previously successfully enrolled a test-retailer account holder
    And the previous response returned a HTTP 202 status code
    And the enrolled account holder has been activated and i know its current balances
    When I post the balance adjustment for a test-retailer account holder passing in all required credentials twice
    Then I receive a HTTP 200 status code in the adjustments response for both
    And The account holder's balance is updated in the database only once


  Scenario: POST a balance adjustment with an invalid idempotency token

    Given I previously successfully enrolled a test-retailer account holder
    And the previous response returned a HTTP 202 status code
    And the enrolled account holder has been activated and i know its current balances
    When I post the balance adjustment for a test-retailer account holder passing in an invalid idempotency token
    Then I receive a HTTP 400 status code response
    And I get a missing_idempotency_header adjustments response body
    And The account holder's balance is not updated in the database
