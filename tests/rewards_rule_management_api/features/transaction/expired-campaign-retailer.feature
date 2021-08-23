@bpl @rrm @transaction
Feature: Post a transaction for an retailer that has only expired campaigns
  As a transaction matching system
  Using the POST /EXPIRED-CAMPAIGNS-RETAILER/transaction endpoint
  I can't store a processed transaction in the RRM database


  Scenario: Send a POST transaction request for an retailer that has only expired campaigns

    Given A active account holder exists for expired-campaign-retailer
    When I send a POST transaction request with the over the threshold payload for a expired-campaign-retailer with the correct token
    Then I get a HTTP 404 rrm no_active_campaigns response
    And The transaction is saved in the transaction database table
    And The transaction is not saved in the processed_transaction database table
