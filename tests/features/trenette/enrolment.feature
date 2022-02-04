@trenette @bpl
Feature: Enrol with Trenette loyalty

    Scenario: Successful enrolment

        Given the trenette retailer exists
        # And has the standard campaigns configured
        Then I can enrol successfully
