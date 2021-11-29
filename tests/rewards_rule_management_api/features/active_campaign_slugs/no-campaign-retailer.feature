@bpl @rrm @active-campaign-slugs
Feature: Get active campaign slugs for a retailer with no campaigns
  As a Customer Management system
  Using the GET /[RetailerRewards.slug]/active-campaign-slugs endpoint
  I will get an error if I make a request to a campaign with no active campaigns

  Scenario: Get no-campaign-retailer active campaign slugs

    Given no-campaign-retailer has no campaigns
    When I send a get /no-campaign-retailer/active-campaign-slugs request with the correct auth token
    Then I receive a HTTP 404 status code response for my GET active-campaign-slugs request
    And I get a no_active_campaigns GET active-campaign-slugs response body
  
  Scenario: Get no-campaign-retailer active campaign slugs using the wrong auth token

    When I send a get /no-campaign-retailer/active-campaign-slugs request with the incorrect auth token
    Then I receive a HTTP 401 status code response for my GET active-campaign-slugs request
    And I get a invalid_token GET active-campaign-slugs response body
