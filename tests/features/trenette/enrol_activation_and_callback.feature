# Created by rupalpatel at 16/02/2022, last updated by Haffi Mazhar at 03/05/2022
Feature: Bink BPL - Ensure a customer can enrol succesfully and that activation and callback is completed
  As a customer
  I want to utilise POST enrol enodpoint
  So I can access to customer management system

  Background:
    Given the trenette retailer exists
    And the retailer's trenette-active-campaign STAMPS campaign starts 10 days ago and ends in a day and is ACTIVE

  @bpl @enrol_callback @bpl-302
  Scenario: Enrol account holder successfull with callback
    When i Enrol a account holder passing in all required and all optional fields
    Then i receive a HTTP 202 status code response
    And the account holder is activated
    And new enrolled account holder's trenette-active-campaign balance is 0
    And an enrolment callback task is saved in the database
    And the enrolment-callback task status is success
    And the balance shown for account holder is 0
