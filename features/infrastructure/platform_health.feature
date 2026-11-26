@infrastructure @api
Feature: Platform health
  As the team running the test suite
  I want to know the platform is up before testing its behaviour
  So that failures point to real defects, not to a broken environment

  @QA-3
  Scenario Outline: The <service> service reports it is healthy
    When the health of the "<service>" service is checked
    Then the service reports it is up

    Examples:
      | service  |
      | booking  |
      | room     |
      | branding |
      | auth     |
      | report   |
      | message  |

  @smoke @QA-4
  Scenario: Visitors can see the available rooms
    When a visitor requests the list of rooms
    Then a list of rooms is returned

  @smoke @QA-5
  Scenario: Visitors can see the B&B details
    When a visitor requests the B&B details
    Then the B&B details include its name
