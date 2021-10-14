@bpl @campaign-status
Feature: Campaign status change
As a the BPL system I want campaign status changes to be handled by the relevant system area so that any
associated entities are updated accordingly

  Scenario: Call the status change endpoint for a test-retailer with a malformed request

    Given test-retailer has at least 1 active campaign(s)
    When I perform a POST operation against the status change endpoint for a test-retailer retailer with a malformed request
    Then I receive a HTTP 400 status code response
    And I get a malformed_request status change response body


  Scenario: Call the status change endpoint where the retailer slug supplied does not exist

    Given test-retailer has at least 1 active campaign(s)
    When I perform a POST operation against the status change endpoint with the correct payload for a Ended status for a NONEXISTANT retailer with a valid auth token
    Then I receive a HTTP 403 status code response
    And I get a invalid_retailer status change response body


  Scenario: Call the status change endpoint where the campaign is not found

    When I perform a POST operation against the status change endpoint for a Ended status for a NONEXISTANT campaign for a test-retailer retailer
    Then I receive a HTTP 404 status code response
    And I get a no_campaign_found status change response body


  Scenario: Send a POST status change request with the wrong payload

    Given test-retailer has at least 1 active campaign(s)
    When I perform a POST operation against the status change endpoint with the incorrect payload for a Ended status for a test-retailer retailer with a valid auth token
    Then I receive a HTTP 422 status code response
    And I get a invalid_content status change response body


  Scenario: Send a POST status change request with an illegal state change

    Given test-retailer has at least 1 active campaign(s)
    When I perform a POST operation against the status change endpoint with the correct payload for a Draft status for a test-retailer retailer with a valid auth token
    Then I receive a HTTP 409 status code response
    And I get a invalid_status_requested status change response body
