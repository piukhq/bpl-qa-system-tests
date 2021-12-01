@bpl @cm @vouchers
Feature: Post a voucher for a incorrect-retailer
  As a VM system
  Using the POST [retailer_slug]/accounts/[account_holder_uuid]/vouchers endpoint
  I can't add an account holder voucher

  
  Scenario: POST a voucher for invalid retailer

    When I POST a voucher expiring in the future for a invalid-retailer account holder with a valid auth token
    Then I receive a HTTP 403 status code response
    And I get a invalid_retailer voucher response body

  
  Scenario: POST a voucher for an invalid retailer with an invalid authorisation token

    When I POST a voucher expiring in the future for a invalid-retailer account holder with a invalid auth token
    Then I receive a HTTP 401 status code response
    And I get a invalid_token voucher response body

  
  Scenario: POST a voucher for an valid retailer with an valid authorisation token for an unknown account holder

    When I POST a voucher expiring in the future for a test-retailer account holder with a valid auth token
    Then I receive a HTTP 404 status code response
    And I get a no_account_found voucher response body
