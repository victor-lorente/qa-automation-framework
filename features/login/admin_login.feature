@login @api
Feature: Admin login
  As the B&B owner
  I want only valid admin credentials to open a session
  So that the admin area stays protected

  @smoke @QA-1
  Scenario: Admin logs in with valid credentials
    When the admin logs in with valid credentials
    Then the login is accepted
    And the session token is valid

  @QA-2
  Scenario Outline: Login is rejected with invalid credentials (<case>)
    When someone logs in with username "<username>" and password "<password>"
    Then the login is rejected as invalid credentials

    Examples:
      | case                | username | password |
      | wrong password      | admin    | nope     |
      | unknown user        | ghost    | password |
      | empty username      |          | password |
      | empty password      | admin    |          |
