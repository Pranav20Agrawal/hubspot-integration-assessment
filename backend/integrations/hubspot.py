# hubspot.py

import os
import json
import secrets
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
import httpx
import asyncio
import base64
from typing import List, Dict, Any
from dotenv import load_dotenv, find_dotenv

from integrations.integration_item import IntegrationItem
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis

# --- Configuration ---
# Load secrets from the .env file at the project's root
load_dotenv(find_dotenv())

CLIENT_ID = os.getenv('HUBSPOT_CLIENT_ID')
CLIENT_SECRET = os.getenv('HUBSPOT_CLIENT_SECRET')
REDIRECT_URI = 'http://localhost:8000/integrations/hubspot/oauth2callback'
SCOPE = 'crm.objects.contacts.read'
AUTHORIZATION_URL = 'https://app.hubspot.com/oauth/authorize'
TOKEN_URL = 'https://api.hubapi.com/oauth/v1/token'


# --- OAuth Functions ---

async def authorize_hubspot(user_id: str, org_id: str) -> str:
    """
    Generates the HubSpot OAuth authorization URL for the user.
    A unique `state` token is created and stored in Redis to prevent CSRF attacks.

    Args:
        user_id: The ID of the user initiating the authorization.
        org_id: The ID of the organization for this user.

    Returns:
        The fully constructed authorization URL for the frontend.
    """
    state_data = {
        'state': secrets.token_urlsafe(32),
        'user_id': user_id,
        'org_id': org_id
    }
    encoded_state = json.dumps(state_data)

    # Store the state in Redis for 10 minutes to validate the callback
    await add_key_value_redis(f'hubspot_state:{org_id}:{user_id}', encoded_state, expire=600)

    auth_url = (
        f"{AUTHORIZATION_URL}?"
        f"client_id={CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"scope={SCOPE}&"
        f"state={encoded_state}"
    )
    return auth_url


async def oauth2callback_hubspot(request: Request) -> HTMLResponse:
    """
    Handles the OAuth2 callback from HubSpot after user authorization.

    Args:
        request: The incoming request object from FastAPI, containing the auth code.

    Returns:
        An HTML response that closes the popup window upon success.
    """
    code = request.query_params.get('code')
    encoded_state = request.query_params.get('state')
    
    if not code or not encoded_state:
        raise HTTPException(status_code=400, detail="HubSpot callback is missing required parameters.")

    state_data = json.loads(encoded_state)
    user_id = state_data.get('user_id')
    org_id = state_data.get('org_id')

    # Verify the state token to prevent CSRF attacks
    saved_state_str = await get_value_redis(f'hubspot_state:{org_id}:{user_id}')
    if not saved_state_str or json.loads(saved_state_str).get('state') != state_data.get('state'):
        raise HTTPException(status_code=400, detail="State mismatch or expired. Authorization failed.")

    # Prepare the payload to exchange the authorization code for an access token
    payload = {
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI,
        'code': code
    }
    
    try:
        # Make the server-to-server request to HubSpot's token endpoint
        async with httpx.AsyncClient() as client:
            response = await client.post(TOKEN_URL, data=payload, headers={'Content-Type': 'application/x-www-form-urlencoded'})
        response.raise_for_status() # Raise an exception for non-2xx responses

    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Service Unavailable: Could not connect to HubSpot.")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"HubSpot API Error: {e.response.text}")

    # Store the newly obtained credentials in Redis temporarily
    credentials = response.json()
    await add_key_value_redis(f'hubspot_credentials:{org_id}:{user_id}', json.dumps(credentials), expire=3600)
    
    # Clean up the used state token
    await delete_key_redis(f'hubspot_state:{org_id}:{user_id}')
    
    # Return a simple HTML page that closes the popup window
    return HTMLResponse(content="<html><script>window.close();</script></html>")


async def get_hubspot_credentials(user_id: str, org_id: str) -> Dict[str, Any]:
    """
    Retrieves HubSpot credentials from Redis for a given user/org.
    This is a single-use function that deletes the credentials after retrieval.

    Args:
        user_id: The ID of the user.
        org_id: The ID of the organization.

    Returns:
        A dictionary containing the OAuth credentials.
    """
    credentials_str = await get_value_redis(f'hubspot_credentials:{org_id}:{user_id}')
    if not credentials_str:
        raise HTTPException(status_code=404, detail='HubSpot credentials not found. Please reconnect.')
    
    credentials = json.loads(credentials_str)
    await delete_key_redis(f'hubspot_credentials:{org_id}:{user_id}')
    
    return credentials


# --- Data Loading and Transformation ---

def _hubspot_contact_to_integration_item(contact_data: dict) -> IntegrationItem:
    """
    Maps a single HubSpot contact object to the standardized IntegrationItem schema.
    Handles cases where contact names may be missing by providing a default name.

    Args:
        contact_data: The JSON dictionary for a single contact from the HubSpot API.

    Returns:
        An IntegrationItem object with mapped fields.
    """
    properties = contact_data.get('properties', {})
    first_name = properties.get('firstname', '')
    last_name = properties.get('lastname', '')
    
    # Combine names and provide a fallback for contacts with no name
    full_name = f"{first_name} {last_name}".strip() or "Untitled Contact"

    return IntegrationItem(
        id=contact_data.get('id'),
        name=full_name,
        type='HubSpot Contact',
        creation_time=contact_data.get('createdAt'),
        last_modified_time=contact_data.get('updatedAt')
    )


async def get_items_hubspot(credentials: str) -> List[IntegrationItem]:
    """
    Fetches the first page of contacts from the HubSpot CRM API using an access token.
    Transforms each contact into a standardized IntegrationItem object.

    Args:
        credentials: A JSON string containing the OAuth credentials.

    Returns:
        A list of IntegrationItem objects representing HubSpot contacts.
    """
    credentials_dict = json.loads(credentials)
    access_token = credentials_dict.get('access_token')

    if not access_token:
        raise HTTPException(status_code=400, detail="Access token is missing from credentials.")

    headers = {'Authorization': f'Bearer {access_token}'}
    contacts_url = 'https://api.hubapi.com/crm/v3/objects/contacts'
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(contacts_url, headers=headers)
        response.raise_for_status()
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Service Unavailable: Could not connect to HubSpot to fetch items.")
    except httpx.HTTPStatusError as e:
        # Pass along the specific error from HubSpot's API
        raise HTTPException(status_code=e.response.status_code, detail=f"HubSpot API Error: {e.response.text}")

    results = response.json().get('results', [])
    list_of_integration_items = [_hubspot_contact_to_integration_item(item) for item in results]
    
    # For demonstration, print the fetched items to the backend console
    print(f"Fetched HubSpot Items: {[item.__dict__ for item in list_of_integration_items]}")
    
    return list_of_integration_items