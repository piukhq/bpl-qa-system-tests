@bpl @vm @rewardimports
Feature: Reward code status updates from 3rd party
  As a retailer I want to be able to handle updates to rewards provided by a 3rd party
  so that existing rewards can be updated in BPL to show status changes.

  Scenario: Handle importing redeemed and/or cancelled reward code status changed from a 3rd party

    Given The reward code provider provides a bulk update file for test-retailer
    Then the file for test-retailer is imported by the reward management system
    And the unallocated reward for test-retailer is marked as deleted and is not imported by the reward management system
    And the file is moved to the archive container by the reward importer
    And the status of the allocated account holder rewards is updated

  Scenario: Check reward files stored on blob storage have unique file names

    Given The reward code provider provides a bulk update file named test_import.csv for test-retailer
    And a update reward file log record exists for the file name test-retailer/reward-updates/test_import.csv
    Then the file is moved to the errors container by the reward importer
