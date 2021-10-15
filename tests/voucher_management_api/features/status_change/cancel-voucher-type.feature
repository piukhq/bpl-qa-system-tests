@bpl @vm @vouchertypestatus
Feature: Cancel a voucher type for a retailer
  As a system
  I want the Voucher management system to be able to remove vouchers for a cancelled/ended campaign
  using the PATCH /{retailer_slug}/vouchers/{voucher_type_slug}/status endpoint

  Scenario: Cancel voucher type for retailer (happy path)

    Given there is an ACTIVE voucher configuration for test-retailer with unallocated vouchers
    When I perform a PATCH operation against the correct voucher type status endpoint instructing a cancelled status change
    Then I receive a HTTP 202 status code response
    And the status of the voucher config is CANCELLED

  Scenario: End voucher type for retailer (happy path)

    Given there is an ACTIVE voucher configuration for test-retailer with unallocated vouchers
    When I perform a PATCH operation against the correct voucher type status endpoint instructing a ended status change
    Then I receive a HTTP 202 status code response
    And the status of the voucher config is ENDED

  Scenario: Cancel voucher type for invalid retailer

    Given there are no voucher configurations for invalid-test-retailer
    When I perform a PATCH operation against the incorrect voucher type status endpoint instructing a cancelled status change
    Then I receive a HTTP 403 status code response

  Scenario: Cancel voucher type for retailer (unknown voucher_type_slug)

    Given there is an ACTIVE voucher configuration for test-retailer with unallocated vouchers
    When I perform a PATCH operation against the incorrect voucher type status endpoint instructing a cancelled status change
    Then I receive a HTTP 404 status code response
    And the status of the voucher config is ACTIVE

  Scenario: Cancel voucher type for retailer (incorrect status transition)

    Given there is an CANCELLED voucher configuration for test-retailer with unallocated vouchers
    When I perform a PATCH operation against the correct voucher type status endpoint instructing a cancelled status change
    Then I receive a HTTP 409 status code response
    And the status of the voucher config is CANCELLED

  Scenario: Alter voucher type for retailer (bad data)

    Given there is an ACTIVE voucher configuration for test-retailer with unallocated vouchers
    When I perform a PATCH operation against the correct voucher type status endpoint instructing a bad-status status change
    Then I receive a HTTP 422 status code response
    And the status of the voucher config is ACTIVE
