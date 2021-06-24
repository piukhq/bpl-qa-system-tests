@bpl @cm @enrol @callbacks @activations
Feature: Bink BPL - Ensure a customer can enrol and that a callback is completed
  As a customer
  I want to utilise POST enrol endpoint
  So I can access to customer management system


  @bpl
  Scenario: Enrol with successful callback

    When I Enrol a test-retailer account holder passing in all required and all optional fields
    Then I receive a HTTP 202 status code in the response
    And an account holder activation is saved in the database
    And the account holder activation completes successfully

  @bpl
  Scenario: Enrol with unsuccessful callback (400)

    When I Enrol a test-retailer account holder passing in all required and all optional fields with a callback URL known to produce an HTTP 400 response
    Then I receive a HTTP 202 status code in the response
    And an account holder activation is saved in the database
    And the account holder activation is marked as FAILED and is not retried

  @bpl
  Scenario: Enrol with successful callback with retries

    When I Enrol a test-retailer account holder passing in all required and all optional fields with a callback URL known to produce 2 consecutive HTTP 500 responses
    Then I receive a HTTP 202 status code in the response
    And an account holder activation is saved in the database
    And the account holder activation completes successfully

  @bpl
  Scenario: Enrol with successful callback with timeout retry

    When I Enrol a test-retailer account holder passing in all required and all optional fields with a callback URL known to timeout after 15 seconds
    Then I receive a HTTP 202 status code in the response
    And an account holder activation is saved in the database
    And the enrolment callback is tried
    And the account holder activation is in IN_PROGRESS state
    And the callback URL is known to produce an HTTP 200 response
    And the account holder activation completes successfully
