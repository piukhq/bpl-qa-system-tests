Feature: Campaign status change
  As a the BPL system I want campaign status changes to be handled by the relevant system area so that any
  associated entities are updated accordingly

  @undertest
  Scenario: Successfully change a campaign status
    Given test-retailer has at least 1 active campaign(s)
    When I perform a POST operation against the status change endpoint for a Ended status for a test-retailer retailer with a valid auth token
    Then I receive a HTTP 200 status code response
    And the campaign status should be updated in Vela
