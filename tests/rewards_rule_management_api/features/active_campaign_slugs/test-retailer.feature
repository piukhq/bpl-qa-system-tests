@bpl @rrm @active-campaign-slugs
Feature: Get test-retailer active campaign slugs
  As a Customer Management system
  Using the GET /[RetailerRewards.slug]/active-campaign-slugs endpoint
  I can get all active campaign slugs setup for test-retailer

  Scenario: Get test-retailer active campaign slugs

    Given test-retailer has at least 2 active campaign(s) and at least 1 non-active campaign(s)
    When I send a get /test-retailer/active-campaign-slugs request with the correct auth token
    Then I receive a HTTP 200 status code response for my GET active-campaign-slugs request
    And I get all the active campaign slugs for test-retailer in my GET active_campaign_slugs response body

  Scenario: Get test-retailer active campaign slugs using the wrong auth token

    When I send a get /test-retailer/active-campaign-slugs request with the incorrect auth token
    Then I receive a HTTP 401 status code response for my GET active-campaign-slugs request
    And I get a invalid_token GET active-campaign-slugs response body
