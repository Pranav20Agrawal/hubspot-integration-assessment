# backend/integrations/test_hubspot.py
"""Unit tests for the HubSpot integration data transformation logic."""

from integrations.hubspot import _hubspot_contact_to_integration_item
from integrations.integration_item import IntegrationItem


def test_hubspot_contact_transformation_happy_path():
    """Verifies that a standard HubSpot contact object is correctly mapped to an IntegrationItem."""
    # Define a sample piece of data mimicking the HubSpot API response
    fake_contact_data = {
        "id": "12345",
        "properties": {
            "firstname": "Jane",
            "lastname": "Doe",
        },
        "createdAt": "2023-01-15T12:00:00.000Z",
        "updatedAt": "2023-08-20T15:30:00.000Z",
    }

    # Call the function we are testing
    result_item = _hubspot_contact_to_integration_item(fake_contact_data)

    # Check that the function's output is exactly what we expect
    assert isinstance(result_item, IntegrationItem)
    assert result_item.id == "12345"
    assert result_item.name == "Jane Doe"
    assert result_item.type == "HubSpot Contact"
    assert result_item.creation_time == "2023-01-15T12:00:00.000Z"
    assert result_item.last_modified_time == "2023-08-20T15:30:00.000Z"


def test_hubspot_contact_transformation_with_no_name():
    """Verifies that a contact with missing name properties is assigned a default name."""
    # Define a contact with missing name properties to test the fallback logic
    fake_contact_data = {
        "id": "67890",
        "properties": {}, # No firstname or lastname
        "createdAt": "2023-02-01T10:00:00.000Z",
        "updatedAt": "2023-09-01T11:00:00.000Z",
    }

    # Call the function
    result_item = _hubspot_contact_to_integration_item(fake_contact_data)

    # Check that the fallback name is used correctly
    assert result_item.id == "67890"
    assert result_item.name == "Untitled Contact"