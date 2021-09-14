@bpl @vm
Feature: Voucher code status updates from 3rd party
  As a retailer I want to be able to handle updates to vouchers provided by a 3rd party
  so that existing vouchers can be updated in BPL to show status changes.
  @test
  Scenario: Handle importing redeemed and/or cancelled voucher code status changed from a 3rd party

    Given The voucher code provider provides a bulk update file for test-retailer
    Then the file for test-retailer is imported by the voucher management system
    And the unallocated voucher for test-retailer is marked as deleted and is not imported by the voucher management system
    And The test-retailer import file is archived by the voucher importer
    And the status of the allocated account holder vouchers is updated
