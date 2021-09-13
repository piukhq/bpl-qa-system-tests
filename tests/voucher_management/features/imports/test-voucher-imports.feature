@bpl @vm
Feature: Voucher code status updates from 3rd party
  As a retailer I want to be able to provide new vouchers for allocation when reward goals are met
  so that customers can be allocated vouchers continuously

  Scenario: Handle importing new voucher codes from a 3rd party

    Given test-retailer provides a csv file in the correct format for the 10percentoff voucher type
    Then only unseen vouchers are imported by the voucher management system
    And the test-retailer voucher import file is archived by the voucher importer
