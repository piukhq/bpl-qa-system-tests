@bpl @metrics
Feature: Bink BPL - Ensure that prometheus is correctly capturing and exposing metrics
  As a Channel User
  Using the costumer management api
  I can see my requests reflected in the /metrics endpoint

  Scenario: Request counter increase with a new http call.

    Given I know the current generic metrics' values
    When I make a request to the enrol endpoint for a test-retailer retailer
    Then I see the HTTP 202 response for the post test-retailer's enrol reflected in the generic metrics

  Scenario: Request counter increase with a new http call even when the call is refused by a middleware.

    Given I know the current generic metrics' values
    When I make a request to the enrol endpoint for a test-retailer retailer with a missing header
    Then I see the HTTP 400 response for the post test-retailer's enrol reflected in the generic metrics
