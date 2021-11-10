@bpl @campaign-status
Feature: Campaign status change
  As a the BPL system I want campaign status changes to be handled by the relevant system area so that any
  associated entities are updated accordingly

  Scenario: Successfully change a campaign status

    Given test-retailer has at least 1 ACTIVE campaign(s)
    When I perform a POST operation against the status change endpoint with the correct payload for a Ended status for a test-retailer retailer with a valid auth token
    Then I receive a HTTP 200 status code response
    And the campaign status should be updated in Vela

  Scenario: Attempt to change a campaign status with an invalid auth token

    Given test-retailer has at least 1 ACTIVE campaign(s)
    When I perform a POST operation against the status change endpoint with the correct payload for a Ended status for a test-retailer retailer with a invalid auth token
    Then I receive a HTTP 401 status code response
    And I get a invalid_token status change response body
