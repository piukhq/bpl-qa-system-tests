# Created by rupalpatel at 14/09/2022
Feature: Bink BPL - Transaction with a reward cap with TRC
    As a customer
    I want to transact some amount
    Where a campaign reward rule has transaction reward cap (TRC) set and allocation window
    So I make sure that rewards issuance are done correctly adhering to TRC

    @bpl @trc @AC-1-2-3 @bpl-690
    Scenario: Pending rewards issued honouring TRC - 1x multiplier - Example 1
        Given the trenette retailer exists with status as TEST
        And the retailer has a REWARD_ISSUANCE email template configured with template id 99999999
        And the email template with template id 99999999 has the following required template variables: reward_url, account_number, first_name
        And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None
        And the retailer has a free-item reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type

        And the retailer's trenette-acc-campaign ACCUMULATOR campaign starts 5 days ago and ends in a day and is ACTIVE
        And the trenette-acc-campaign campaign has an earn rule with a threshold of 0, an increment of 0, a multiplier of 1 and max amount of 0
        And the trenette-acc-campaign campaign has reward rule with reward goal: 10000, allocation window: 1 and reward cap: 2

        And there is 5 rewards configured for the free-item reward config, with allocation status set to false and deleted status set to false

        And an active account holder exists for the retailer
        And the account holder's trenette-acc-campaign balance is 0
        When BPL receives a transaction for the account holder for the amount of 55000 pennies
        Then BPL responds with a HTTP 200 and awarded message
        And the account holder balance shown for trenette-acc-campaign is 0
        And the account holder has 1 pending reward records for the trenette-acc-campaign campaign
        And the account holder's 1st pending reward record for trenette-acc-campaign has count of 2, value of 10000 and total cost to user of 55000 with a conversion date in a day
        And 2 pending rewards are available to the account holder for the trenette-acc-campaign campaign

        When BPL receives a transaction for the account holder for the amount of -20000 pennies
        Then BPL responds with a HTTP 200 and refund_accepted message
        And the account holder balance shown for trenette-acc-campaign is 0
        And the account holder has 1 pending reward records for the trenette-acc-campaign campaign
        And the account holder's 1st pending reward record for trenette-acc-campaign has count of 2, value of 10000 and total cost to user of 35000 with a conversion date in a day
        And 2 pending rewards are available to the account holder for the trenette-acc-campaign campaign

        When BPL receives a transaction for the account holder for the amount of -20000 pennies
        Then BPL responds with a HTTP 200 and refund_accepted message
        And the account holder balance shown for trenette-acc-campaign is 5000
        And the account holder has 1 pending reward records for the trenette-acc-campaign campaign
        And the account holder's 1st pending reward record for trenette-acc-campaign has count of 1, value of 10000 and total cost to user of 10000 with a conversion date in a day
        And 1 pending rewards are available to the account holder for the trenette-acc-campaign campaign

    @bpl @trc @AC-4-5 @bpl-690
    Scenario: Pending rewards issued honouring TRC - 1x multiplier - Example 2
        Given the trenette retailer exists with status as TEST
        And the retailer has a REWARD_ISSUANCE email template configured with template id 99999999
        And the email template with template id 99999999 has the following required template variables: reward_url, account_number, first_name
        And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None
        And the retailer has a free-item reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type

        And the retailer's trenette-acc-campaign ACCUMULATOR campaign starts 5 days ago and ends in a day and is ACTIVE
        And the trenette-acc-campaign campaign has an earn rule with a threshold of 0, an increment of 0, a multiplier of 1 and max amount of 0
        And the trenette-acc-campaign campaign has reward rule with reward goal: 10000, allocation window: 1 and reward cap: 2

        And there is 5 rewards configured for the free-item reward config, with allocation status set to false and deleted status set to false

        And an active account holder exists for the retailer
        And the account holder's trenette-acc-campaign balance is 0
        When BPL receives a transaction for the account holder for the amount of 7500 pennies
        Then the account holder balance shown for trenette-acc-campaign is 7500
        When BPL receives a transaction for the account holder for the amount of 25000 pennies
        Then BPL responds with a HTTP 200 and awarded message
        And the account holder balance shown for trenette-acc-campaign is 7500
        And the account holder has 1 pending reward records for the trenette-acc-campaign campaign
        And the account holder's 1st pending reward record for trenette-acc-campaign has count of 2, value of 10000 and total cost to user of 25000 with a conversion date in a day
        And 2 pending rewards are available to the account holder for the trenette-acc-campaign campaign

        When BPL receives a transaction for the account holder for the amount of -20000 pennies
        Then BPL responds with a HTTP 200 and refund_accepted message
        And the account holder balance shown for trenette-acc-campaign is 2500
        And the account holder has 1 pending reward records for the trenette-acc-campaign campaign
        And the account holder's 1st pending reward record for trenette-acc-campaign has count of 1, value of 10000 and total cost to user of 10000 with a conversion date in a day
        And 1 pending rewards are available to the account holder for the trenette-acc-campaign campaign


    @bpl @trc @AC-6 @bpl-690
    Scenario: Pending rewards issued honouring TRC - 1x multiplier - Example 3
        Given the trenette retailer exists with status as TEST
        And the retailer has a REWARD_ISSUANCE email template configured with template id 99999999
        And the email template with template id 99999999 has the following required template variables: reward_url, account_number, first_name
        And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None
        And the retailer has a free-item reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type

        And the retailer's trenette-acc-campaign ACCUMULATOR campaign starts 5 days ago and ends in a day and is ACTIVE
        And the trenette-acc-campaign campaign has an earn rule with a threshold of 0, an increment of 0, a multiplier of 1 and max amount of 0
        And the trenette-acc-campaign campaign has reward rule with reward goal: 10000, allocation window: 1 and reward cap: 2

        And there is 5 rewards configured for the free-item reward config, with allocation status set to false and deleted status set to false

        And an active account holder exists for the retailer
        And the account holder's trenette-acc-campaign balance is 0
        When BPL receives a transaction for the account holder for the amount of 7500 pennies
        Then the account holder balance shown for trenette-acc-campaign is 7500
        When BPL receives a transaction for the account holder for the amount of 15000 pennies
        Then BPL responds with a HTTP 200 and awarded message
        And the account holder balance shown for trenette-acc-campaign is 2500
        And the account holder has 1 pending reward records for the trenette-acc-campaign campaign
        And the account holder's 1st pending reward record for trenette-acc-campaign has count of 2, value of 10000 and total cost to user of 20000 with a conversion date in a day
        And 2 pending rewards are available to the account holder for the trenette-acc-campaign campaign

    @bpl @trc @AC-7 @bpl-690
    Scenario:  Pending rewards issued honouring TRC - 2x multiplier - Example 1
        Given the trenette retailer exists with status as TEST
        And the retailer has a REWARD_ISSUANCE email template configured with template id 99999999
        And the email template with template id 99999999 has the following required template variables: reward_url, account_number, first_name
        And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None
        And the retailer has a free-item reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type

        And the retailer's trenette-acc-campaign ACCUMULATOR campaign starts 5 days ago and ends in a day and is ACTIVE
        And the trenette-acc-campaign campaign has an earn rule with a threshold of 0, an increment of 0, a multiplier of 2 and max amount of 0
        And the trenette-acc-campaign campaign has reward rule with reward goal: 10000, allocation window: 1 and reward cap: 2

        And there is 5 rewards configured for the free-item reward config, with allocation status set to false and deleted status set to false

        And an active account holder exists for the retailer
        And the account holder's trenette-acc-campaign balance is 0
        When BPL receives a transaction for the account holder for the amount of 50000 pennies
        Then BPL responds with a HTTP 200 and awarded message
        Then the account holder balance shown for trenette-acc-campaign is 0
        And the account holder has 1 pending reward records for the trenette-acc-campaign campaign
        And the account holder's 1st pending reward record for trenette-acc-campaign has count of 2, value of 10000 and total cost to user of 100000 with a conversion date in a day

        When BPL receives a transaction for the account holder for the amount of -25000 pennies
        Then BPL responds with a HTTP 200 and refund_accepted message
        And the account holder balance shown for trenette-acc-campaign is 0
        And the account holder has 1 pending reward records for the trenette-acc-campaign campaign
        And the account holder's 1st pending reward record for trenette-acc-campaign has count of 2, value of 10000 and total cost to user of 50000 with a conversion date in a day
        And 2 pending rewards are available to the account holder for the trenette-acc-campaign campaign

    @bpl @trc @AC-8 @bpl-690
    Scenario:  Pending rewards issued honouring TRC - 2x multiplier - Coversation day 5 in future (Confluence page Example-4)
        Given the trenette retailer exists with status as TEST
        And the retailer has a REWARD_ISSUANCE email template configured with template id 99999999
        And the email template with template id 99999999 has the following required template variables: reward_url, account_number, first_name
        And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None
        And the retailer has a free-item reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type

        And the retailer's trenette-acc-campaign ACCUMULATOR campaign starts 5 days ago and ends in a day and is ACTIVE
        And the trenette-acc-campaign campaign has an earn rule with a threshold of 0, an increment of 0, a multiplier of 2 and max amount of 0
        And the trenette-acc-campaign campaign has reward rule with reward goal: 10000, allocation window: 5 and reward cap: 2

        And there is 5 rewards configured for the free-item reward config, with allocation status set to false and deleted status set to false

        And an active account holder exists for the retailer
        And the account holder's trenette-acc-campaign balance is 0
        When BPL receives a transaction for the account holder for the amount of 5500 pennies
        Then BPL responds with a HTTP 200 and awarded message
        And the account holder balance shown for trenette-acc-campaign is 1000
        And the account holder has 1 pending reward records for the trenette-acc-campaign campaign
        And the account holder's 1st pending reward record for trenette-acc-campaign has count of 1, value of 10000 and total cost to user of 10000 with a conversion date in 5 days

        When BPL receives a transaction for the account holder for the amount of -5000 pennies
        Then BPL responds with a HTTP 200 and refund_accepted message
        And the account holder balance shown for trenette-acc-campaign is 1000
        And 0 pending rewards are available to the account holder for the trenette-acc-campaign campaign

        When BPL receives a transaction for the account holder for the amount of 50000 pennies
        Then BPL responds with a HTTP 200 and awarded message
        And the account holder balance shown for trenette-acc-campaign is 1000
        And the account holder has 1 pending reward records for the trenette-acc-campaign campaign
        And the account holder's 1st pending reward record for trenette-acc-campaign has count of 2, value of 10000 and total cost to user of 100000 with a conversion date in 5 days

        When BPL receives a transaction for the account holder for the amount of -25000 pennies
        Then BPL responds with a HTTP 200 and refund_accepted message
        And the account holder balance shown for trenette-acc-campaign is 1000
        And the account holder's 1st pending reward record for trenette-acc-campaign has count of 2, value of 10000 and total cost to user of 50000 with a conversion date in 5 days


    @bpl @trc @AC-9 @bpl-690
    Scenario:  Pending rewards issued honouring TRC - 1x multiplier - (Confluence page Example-3)
        Given the trenette retailer exists with status as TEST
        And the retailer has a REWARD_ISSUANCE email template configured with template id 99999999
        And the email template with template id 99999999 has the following required template variables: reward_url, account_number, first_name
        And a PRE_LOADED fetch type is configured for the current retailer with an agent config of None
        And the retailer has a free-item reward config configured with validity_days: 30, and a status of ACTIVE and a PRE_LOADED fetch type

        And the retailer's trenette-acc-campaign ACCUMULATOR campaign starts 5 days ago and ends in a day and is ACTIVE
        And the trenette-acc-campaign campaign has an earn rule with a threshold of 0, an increment of 0, a multiplier of 1 and max amount of 0
        And the trenette-acc-campaign campaign has reward rule with reward goal: 10000, allocation window: 5 and reward cap: 2

        And there is 5 rewards configured for the free-item reward config, with allocation status set to false and deleted status set to false

        And an active account holder exists for the retailer
        And the account holder's trenette-acc-campaign balance is 0
        When BPL receives a transaction for the account holder for the amount of 5000 pennies
        Then BPL responds with a HTTP 200 and awarded message
        And the account holder balance shown for trenette-acc-campaign is 5000

        When BPL receives a transaction for the account holder for the amount of 2500 pennies
        Then BPL responds with a HTTP 200 and awarded message
        And the account holder balance shown for trenette-acc-campaign is 7500

        When BPL receives a transaction for the account holder for the amount of 25000 pennies
        Then BPL responds with a HTTP 200 and awarded message
        And the account holder balance shown for trenette-acc-campaign is 7500
        And the account holder has 1 pending reward records for the trenette-acc-campaign campaign
        And the account holder's 1st pending reward record for trenette-acc-campaign has count of 2, value of 10000 and total cost to user of 25000 with a conversion date in 5 days

        When BPL receives a transaction for the account holder for the amount of 7500 pennies
        Then BPL responds with a HTTP 200 and awarded message
        And the account holder balance shown for trenette-acc-campaign is 5000
        And the account holder has 2 pending reward records for the trenette-acc-campaign campaign
        And the account holder's 1st pending reward record for trenette-acc-campaign has count of 2, value of 10000 and total cost to user of 25000 with a conversion date in 5 days
        And the account holder's 2nd pending reward record for trenette-acc-campaign has count of 1, value of 10000 and total cost to user of 10000 with a conversion date in 5 days
        And 3 pending rewards are available to the account holder for the trenette-acc-campaign campaign

        When BPL receives a transaction for the account holder for the amount of 15000 pennies
        Then BPL responds with a HTTP 200 and awarded message
        And the account holder balance shown for trenette-acc-campaign is 0
        And the account holder has 3 pending reward records for the trenette-acc-campaign campaign
        And the account holder's 1st pending reward record for trenette-acc-campaign has count of 2, value of 10000 and total cost to user of 25000 with a conversion date in 5 days
        And the account holder's 2nd pending reward record for trenette-acc-campaign has count of 1, value of 10000 and total cost to user of 10000 with a conversion date in 5 days
        And the account holder's 3rd pending reward record for trenette-acc-campaign has count of 2, value of 10000 and total cost to user of 20000 with a conversion date in 5 days
        And 5 pending rewards are available to the account holder for the trenette-acc-campaign campaign
