@bpl @cm @vouchers
Feature: Post a voucher for a test-retailer
  As a VM system
  Using the POST [retailer_slug]/accounts/[account_holder_uuid]/vouchers endpoint
  I can add an account holder voucher

  Scenario: Successfully POST a voucher

    Given I previously successfully enrolled a test-retailer account holder
    And I received a HTTP 202 status code response
    And the enrolled account holder has been activated
    And I POST a voucher expiring in the future for a test-retailer account holder with a valid auth token
    Then I receive a HTTP 200 status code in the voucher response
    When I send a get /accounts request for a test-retailer account holder by UUID
    Then the returned voucher's status is issued and the voucher data is well formed

  Scenario: Voucher status is EXPIRED when expiry_date is in the past

    Given I previously successfully enrolled a test-retailer account holder
    And I received a HTTP 202 status code response
    And the enrolled account holder has been activated
    And I POST a voucher expiring in the past for a test-retailer account holder with a valid auth token
    Then I receive a HTTP 200 status code in the voucher response
    When I send a get /accounts request for a test-retailer account holder by UUID
    Then the returned voucher's status is expired and the voucher data is well formed