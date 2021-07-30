@bpl @cm @voucherstatus
Feature: Bink BPL - Ensure that as a bpl service I can update an account holder's voucher status
  As a bpl service
  Using the PATCH /test-retailer/vouchers/{voucher_id}/status endpoint
  I can update the requested voucher status

  Scenario: Update a voucher's status to redeemed
    Given A active account holder exists for test-retailer
    And The account holder has an issued voucher
    When I PATCH a voucher's status to redeemed for a test-retailer using a valid auth token
    Then I receive a HTTP 200 status code in the vouchers status response
    And I get a success voucher status response body
    And The account holders will have the voucher's status updated in their account

  Scenario: Update a voucher's status to cancelled
    Given A active account holder exists for test-retailer
    And The account holder has an issued voucher
    When I PATCH a voucher's status to cancelled for a test-retailer using a valid auth token
    Then I receive a HTTP 200 status code in the vouchers status response
    And I get a success voucher status response body
    And The account holders will have the voucher's status updated in their account

  Scenario: Update a non issued voucher's status
    Given A active account holder exists for test-retailer
    And The account holder has an non issued voucher
    When I PATCH a voucher's status to redeemed for a test-retailer using a valid auth token
    Then I receive a HTTP 202 status code in the vouchers status response
    And I get a status_not_changed voucher status response body

  Scenario: Update a voucher's status to a non supported value
    Given A active account holder exists for test-retailer
    And The account holder has an issued voucher
    When I PATCH a voucher's status to a-wrong-value for a test-retailer using a valid auth token
    Then I receive a HTTP 400 status code in the vouchers status response
    And I get a invalid_status voucher status response body
    And The account holders will not have the voucher's status updated in their account

  Scenario: Update a non existing voucher's status
    Given There is no voucher to update
    When I PATCH a voucher's status to redeemed for a test-retailer using a valid auth token
    Then I receive a HTTP 404 status code in the vouchers status response
    And I get a no_voucher_found voucher status response body



