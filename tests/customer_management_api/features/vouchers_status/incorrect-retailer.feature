@bpl @cm @voucherstatus
Feature: Bink BPL - Ensure that as a bpl service I can't update an account holder's voucher status using a incorrect-retailer
  As a bpl service
  Using the PATCH /test-retailer/vouchers/{voucher_id}/status endpoint
  I can't update the requested voucher status using a incorrect-retailer

  
  Scenario: Update a voucher's status to redeemed for a incorrect-retailer
    Given A active account holder exists for test-retailer
    And The account holder has an issued voucher
    When I PATCH a voucher's status to redeemed for a incorrect-retailer using a valid auth token
    Then I receive a HTTP 403 status code in the vouchers status response
    And I get a invalid_retailer voucher status response body

  
  Scenario: Update a voucher's status to redeemed for a incorrect-retailer with an invalid token
    Given A active account holder exists for test-retailer
    And The account holder has an issued voucher
    When I PATCH a voucher's status to redeemed for a incorrect-retailer using a invalid auth token
    Then I receive a HTTP 401 status code in the vouchers status response
    And I get a invalid_token voucher status response body
