@bpl @cm @adjustments
Feature: Post a balance adjustment for a incorrect-retailer
  As a RRM system
  Using the POST [retailer_slug]/accounts/[account_holder_uuid]/adjustments endpoint
  I can't adjust an account holder balance

  Scenario: POST a balance adjustment for invalid retailer

    When I post the balance adjustment for a invalid-retailer account holder with a valid auth token
    Then I receive a HTTP 403 status code in the adjustments response
    And I get a invalid_retailer adjustments response body

  Scenario: POST a balance adjustment for an invalid retailer with an invalid authorisation token

    When I post the balance adjustment for a invalid-retailer account holder with a invalid auth token
    Then I receive a HTTP 401 status code in the adjustments response
    And I get a invalid_token adjustments response body
