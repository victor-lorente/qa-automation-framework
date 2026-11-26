@login
Feature: Admin login
  As the B&B owner
  I want only valid admin credentials to open a session
  So that the admin area stays protected

  @api @smoke @QA-1
  Scenario: Admin logs in with valid credentials
    When the admin logs in with valid credentials
    Then the login is accepted
    And the session token is valid

  @api @QA-2
  Scenario Outline: Login is rejected with invalid credentials (<case>)
    When someone logs in with username "<username>" and password "<password>"
    Then the login is rejected as invalid credentials

    Examples:
      | case                | username | password |
      | wrong password      | admin    | nope     |
      | unknown user        | ghost    | password |
      | empty username      |          | password |
      | empty password      | admin    |          |

  @ui @smoke @QA-14
  Scenario: Admin logs in through the login form
    When the admin logs in through the login form
    Then the admin area is shown

  @ui @QA-15
  Scenario: The login form rejects a wrong password
    When the admin logs in through the login form with password "wrong"
    Then the login form reports invalid credentials
    And the admin area is not shown
