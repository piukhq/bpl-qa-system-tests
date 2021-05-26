@bpl @cm @enrol @callbacks
Feature: Bink BPL - Ensure a customer can enrol and that a callback is completed
  As a customer
  I want to utilise POST enrol endpoint
  So I can access to customer management system


  @bpl
  Scenario: Enrol with successful callback

    When I Enrol a test-retailer account holder passing in all required and all optional fields
    Then I receive a HTTP 202 status code in the response
    And an enrolment callback is saved in the database
    And the enrolment callback completes successfully

  @bpl
  Scenario: Enrol with unsuccessful callback (400)

    When I Enrol a test-retailer account holder passing in all required and all optional fields
    And the callback URL is known to produce an HTTP 400 response
    Then I receive a HTTP 202 status code in the response
    And an enrolment callback is saved in the database
    And the enrolment callback is marked as failed and is not retried

  @bpl
  Scenario: Enrol with successful callback with retries

    When I Enrol a test-retailer account holder passing in all required and all optional fields
    And the callback URL is known to produce 2 consecutive HTTP 500 error responses
    Then I receive a HTTP 202 status code in the response
    And an enrolment callback is saved in the database
    And the enrolment callback completes successfully

  @bpl
  Scenario: Enrol with successful callback with timeout retry

    When I Enrol a test-retailer account holder passing in all required and all optional fields
    And the callback URL is known to timeout after 20 seconds
    Then I receive a HTTP 202 status code in the response
    And an enrolment callback is saved in the database
    And the enrolment callback is tried
    And the enrolment callback is in PENDING state
    And the callback URL is known to produce an HTTP 200 response
    And the enrolment callback completes successfully
