# Created by rupalpatel at 16/02/2022
@enrol @test @bpl
Feature: Bink BPL - Ensure a customer can enrol succesfully and that activation and callback is completed
  As a customer
  I want to utilise POST enrol enodpoint
  So I can access to customer management system

  Scenario: Enrol account holder successfull with callback

    Given the trenette retailer exists
    And has the standard campaigns configured
    When I Enrol a trenette account holder passing in all required and all optional fields
    Then I receive a HTTP 202 status code response
    And the account holder is activated
    And an enrolment callback task is saved in the database

