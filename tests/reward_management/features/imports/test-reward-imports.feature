@bpl @vm @rewardimports
Feature: Reward code status updates from 3rd party
  As a retailer I want to be able to provide new rewards for allocation when reward goals are met
  so that customers can be allocated rewards continuously

  @thisone
  Scenario: Handle importing new reward codes from a 3rd party

    Given test-retailer has pre-existing rewards for the 10percentoff reward slug
    And test-retailer provides a csv file in the correct format for the 10percentoff reward slug
    Then only unseen rewards are imported by the reward management system
    And the file is moved to the archive container by the reward importer

  Scenario: Handle importing new reward codes from a 3rd party for an unknown reward type

    Given test-retailer provides a csv file in the correct format for the unknown-reward-type reward slug
    Then the file is moved to the errors container by the reward importer
    And the reward codes are not imported
