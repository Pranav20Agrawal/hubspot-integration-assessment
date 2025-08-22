# backend/integrations/test_hubspot.py

from integrations.hubspot import _hubspot_contact_to_integration_item
from integrations.integration_item import IntegrationItem

def test_hubspot_contact_transformation_happy_path():
    """
    Tests that a standard HubSpot contact object is correctly
    transformed into our IntegrationItem data structure.
    """
    # 1. ARRANGE: Define a sample piece of data from the HubSpot API.
    fake_contact_data = {
        "id": "12345",
        "properties": {
            "firstname": "Jane",
            "lastname": "Doe",
        },
        "createdAt": "2023-01-15T12:00:00.000Z",
        "updatedAt": "2023-08-20T15:30:00.000Z",
    }

    # 2. ACT: Call the function we want to test with the sample data.
    result_item = _hubspot_contact_to_integration_item(fake_contact_data)

    # 3. ASSERT: Check that the function's output is exactly what we expect.
    assert isinstance(result_item, IntegrationItem)
    assert result_item.id == "12345"
    assert result_item.name == "Jane Doe"
    assert result_item.type == "HubSpot Contact"
    assert result_item.creation_time == "2023-01-15T12:00:00.000Z"
    assert result_item.last_modified_time == "2023-08-20T15:30:00.000Z"

def test_hubspot_contact_transformation_with_no_name():
    """
    Tests the fallback behavior when a contact has no name properties
    to ensure the code doesn't crash and provides a sensible default.
    """
    # 1. ARRANGE: Create a contact with missing name properties.
    fake_contact_data = {
        "id": "67890",
        "properties": {}, # No firstname or lastname
        "createdAt": "2023-02-01T10:00:00.000Z",
        "updatedAt": "2023-09-01T11:00:00.000Z",
    }

    # 2. ACT
    result_item = _hubspot_contact_to_integration_item(fake_contact_data)

    # 3. ASSERT
    assert result_item.id == "67890"
    assert result_item.name == "Untitled Contact" # Check the fallback name is used