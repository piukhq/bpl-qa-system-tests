@bpl @vm @voucherimports
Feature: Voucher code status updates from 3rd party
  As a retailer I want to be able to provide new vouchers for allocation when reward goals are met
  so that customers can be allocated vouchers continuously

  Scenario: Handle importing new voucher codes from a 3rd party

    Given test-retailer has pre-existing vouchers for the 10percentoff voucher type
    And test-retailer provides a csv file in the correct format for the 10percentoff voucher type
    Then only unseen vouchers are imported by the voucher management system
    And the file is moved to the archive container by the voucher importer

  Scenario: Handle importing new voucher codes from a 3rd party for an unknown voucher type

    Given test-retailer provides a csv file in the correct format for the unknown-voucher-type voucher type
    Then the file is moved to the errors container by the voucher importer
    And the voucher codes are not imported
