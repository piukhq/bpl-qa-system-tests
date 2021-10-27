@bpl @vm
Feature: Allocate a specific voucher type to an account
  As a system
  I want the Voucher management system to be able to send and receive requests and responses
  from other BPL internal systems so that a customer can be issued a voucher and their Account updated.
  Using the POST /{retailer_slug}/vouchers/{voucher_type_slug}/allocation endpoint

  Scenario: Allocate a specific voucher type to an account for test-retailer with a valid voucher_type_slug

    Given A active account holder exists for test-retailer
    And there are at least 1 voucher configs for test-retailer
    And there are vouchers that can be allocated for the existing voucher configs
    When I perform a POST operation against the allocation endpoint for a test-retailer account holder with a valid auth token
    Then I receive a HTTP 202 status code response
    And a Voucher code will be allocated asynchronously
    And the expiry date is calculated using the expiry window for the voucher_type_slug from the Voucher Management Config
    And a POST to /vouchers will be made to update the users account with the voucher allocation


  Scenario:  Allocate a specific voucher type to an account for test-retailer with an invalid voucher_type_slug

    Given A active account holder exists for test-retailer
    And there are at least 1 voucher configs for test-retailer
    And there are vouchers that can be allocated for the existing voucher configs
    When I perform a POST operation against the allocation endpoint for a test-retailer account holder with a invalid auth token
    Then I receive a HTTP 401 status code response
    And I get a invalid_token voucher allocation response body
