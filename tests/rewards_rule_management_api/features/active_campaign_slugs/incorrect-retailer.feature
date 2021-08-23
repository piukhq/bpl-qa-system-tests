@bpl @rrm @active-campaign-slugs
Feature: Get active campaign slugs for an invalid retailer
  As a Customer Management system
  Using the GET /[RetailerRewards.slug]/active-campaign-slugs endpoint
  I can't get any active campaign slugs using an invalid retailer slug

  Scenario: Get active campaign slugs using an invalid retailer slug

    When I send a get /invalid-retailer/active-campaign-slugs request with the correct auth token
    Then I receive a HTTP 403 status code response for my GET active-campaign-slugs request
    And I get a invalid_retailer GET active-campaign-slugs response body

  Scenario: GET active campaign slugs using an invalid retailer and invalid authorisation token

    When I send a get /invalid-retailer/active-campaign-slugs request with the incorrect auth token
    Then I receive a HTTP 401 status code response for my GET active-campaign-slugs request
    And I get a invalid_token GET active-campaign-slugs response body
