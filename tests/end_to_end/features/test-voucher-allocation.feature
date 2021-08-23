@bpl @endtoend
Feature: Allocation of voucher once reward goal met

  Scenario: Successfully POST an awardable transaction that increases the balance above the reward goal for the active campaign

    Given test-retailer has an active campaign with the slug test-campaign-1 where the earn increment is not the transaction value
    And A active account holder exists for test-retailer
    And the campaign has an earn rule threshold and a reward goal with the same value for a voucher type of 10percentoff
    And there are unallocated vouchers for the campaign for a voucher type of 10percentoff
    When I send a POST transaction request with a transaction value matching the reward goal for the campaign
    Then I get a HTTP 200 rrm awarded response
    And A voucher is allocated to the account holder
    And the voucher expiry date is the correct number of days after the issued date
    And The account holder balance is updated
