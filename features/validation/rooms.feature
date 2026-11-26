@validation
Feature: Room management
  As the B&B owner
  I want to manage the rooms I offer
  So that visitors always see accurate rooms and prices

  @api @mutating @smoke @QA-6
  Scenario: Admin creates a room and visitors can see it
    Given the admin is logged in
    When the admin creates a "Double" room priced at 150 with features "WiFi, TV"
    Then the room is created
    And visitors see the new room with its details

  @api @mutating @QA-7
  Scenario Outline: Rooms can be priced at the limits of the allowed range (<price>)
    Given the admin is logged in
    When the admin creates a "Single" room priced at <price> with features ""
    Then the room is created

    Examples:
      | price |
      | 1     |
      | 999   |

  # Mutating: if validation regressed, the "rejected" room would actually be created.
  @api @mutating @QA-8
  Scenario Outline: Rooms with invalid data are rejected (<case>)
    Given the admin is logged in
    When the admin creates a room with <field> "<value>"
    Then the room is rejected with the message "<message>"

    Examples:
      | case           | field | value     | message                                                                      |
      | empty name     | name  |           | Room name must be set                                                        |
      | unknown type   | type  | Penthouse | Type can only contain the room options Single, Double, Twin, Family or Suite |
      | price too low  | price | 0         | must be greater than or equal to 1                                           |
      | price too high | price | 1000      | must be less than or equal to 999                                            |

  @api @mutating @QA-9
  Scenario: Visitors cannot create rooms
    When a visitor tries to create a room
    Then the request is forbidden

  @api @mutating @QA-10
  Scenario: Rooms cannot be created with an invalid session
    When someone with an invalid session tries to create a room
    Then the request is forbidden

  @api @QA-11
  Scenario: Visitors can see the details of a room
    Given there is at least one room
    When a visitor requests the details of that room
    Then the details of that room are returned

  @api @mutating @QA-12
  Scenario: Admin deletes a room
    Given the admin has created a room
    When the admin deletes that room
    Then the room no longer appears in the list of rooms

  @api @mutating @bug_deleted_room_500 @QA-13
  Scenario: A deleted room is reported as not found
    Given the admin has created a room
    And the admin has deleted that room
    When a visitor requests the details of that room
    Then the room is reported as not found

  @hybrid @mutating @QA-16
  Scenario: Admin sees a room created through the API in the room list
    Given the admin has created a room
    And the admin is signed in to the admin area
    When the admin opens the room list
    Then the room is listed with its type and price
