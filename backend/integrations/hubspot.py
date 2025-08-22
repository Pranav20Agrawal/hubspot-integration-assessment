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
# Make sure to import find_dotenv
from dotenv import load_dotenv, find_dotenv

from integrations.integration_item import IntegrationItem
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis

# --- Configuration ---
# Explicitly find and load the .env file
load_dotenv(find_dotenv())

CLIENT_ID = os.getenv('HUBSPOT_CLIENT_ID')
CLIENT_SECRET = os.getenv('HUBSPOT_CLIENT_SECRET')

# Add this temporary line for debugging:
print(f"--- DEBUG --- Loaded Client ID is: {CLIENT_ID}")

REDIRECT_URI = 'http://localhost:8000/integrations/hubspot/oauth2callback'
SCOPE = 'crm.objects.contacts.read'
AUTHORIZATION_URL = 'https://app.hubspot.com/oauth/authorize'
TOKEN_URL = 'https://api.hubapi.com/oauth/v1/token'


# --- OAuth Functions ---

async def authorize_hubspot(user_id: str, org_id: str) -> str:
    """
    Creates the initial authorization URL to send the user to HubSpot for authentication.

    This URL includes a secure state token to prevent CSRF attacks and specifies the
    permissions (scopes) our application is requesting.

    Args:
        user_id: The ID of the user initiating the authorization.
        org_id: The ID of the organization for this user.

    Returns:
        The fully constructed authorization URL for the frontend to redirect to.
    """
    state_data = {
        'state': secrets.token_urlsafe(32),
        'user_id': user_id,
        'org_id': org_id
    }
    encoded_state = json.dumps(state_data)

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

    It verifies the state token, exchanges the temporary authorization code
    for a permanent access token, and stores the credentials securely.

    Args:
        request: The incoming request object from FastAPI, containing query parameters.

    Returns:
        An HTML response that closes the popup window upon success.
    """
    code = request.query_params.get('code')
    encoded_state = request.query_params.get('state')
    
    if not code or not encoded_state:
        raise HTTPException(status_code=400, detail="Missing code or state from HubSpot callback.")

    state_data = json.loads(encoded_state)
    user_id = state_data.get('user_id')
    org_id = state_data.get('org_id')

    saved_state_str = await get_value_redis(f'hubspot_state:{org_id}:{user_id}')
    if not saved_state_str:
        raise HTTPException(status_code=400, detail="State has expired or is invalid.")

    saved_state_data = json.loads(saved_state_str)
    if saved_state_data.get('state') != state_data.get('state'):
        raise HTTPException(status_code=400, detail="State mismatch. CSRF attack may have been attempted.")

    payload = {
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI,
        'code': code
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(TOKEN_URL, data=payload, headers={'Content-Type': 'application/x-www-form-urlencoded'})
        
        response.raise_for_status()

    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Service Unavailable: Could not connect to HubSpot to exchange token. {e}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"HubSpot API error: {e.response.text}")

    credentials = response.json()
    await add_key_value_redis(f'hubspot_credentials:{org_id}:{user_id}', json.dumps(credentials), expire=3600)
    await delete_key_redis(f'hubspot_state:{org_id}:{user_id}')
    
    return HTMLResponse(content="<html><script>window.close();</script></html>")


async def get_hubspot_credentials(user_id: str, org_id: str) -> Dict[str, Any]:
    """
    Retrieves the stored HubSpot credentials for a user from Redis.

    This is a single-use retrieval; the credentials are deleted from Redis
    after being fetched to ensure they are only held temporarily.

    Args:
        user_id: The ID of the user.
        org_id: The ID of the organization.

    Returns:
        A dictionary containing the OAuth credentials (access_token, etc.).
    """
    credentials_str = await get_value_redis(f'hubspot_credentials:{org_id}:{user_id}')
    if not credentials_str:
        raise HTTPException(status_code=404, detail='HubSpot credentials not found. Please reconnect.')
    
    credentials = json.loads(credentials_str)
    await delete_key_redis(f'hubspot_credentials:{org_id}:{user_id}')
    
    return credentials


# --- Data Loading and Transformation Functions ---

def _hubspot_contact_to_integration_item(contact_data: dict) -> IntegrationItem:
    """
    Transforms a raw HubSpot contact object into a standardized IntegrationItem.

    Args:
        contact_data: The JSON dictionary for a single contact from the HubSpot API.

    Returns:
        An IntegrationItem object with mapped fields.
    """
    properties = contact_data.get('properties', {})
    first_name = properties.get('firstname', '')
    last_name = properties.get('lastname', '')
    
    full_name = f"{first_name} {last_name}".strip()
    if not full_name:
        full_name = "Untitled Contact"

    return IntegrationItem(
        id=contact_data.get('id'),
        name=full_name,
        type='HubSpot Contact',
        creation_time=contact_data.get('createdAt'),
        last_modified_time=contact_data.get('updatedAt')
    )


async def get_items_hubspot(credentials: str) -> List[IntegrationItem]:
    """
    Fetches a list of contacts from HubSpot using the provided credentials.

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
    
    list_of_integration_items = []
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(contacts_url, headers=headers)
        
        response.raise_for_status()

    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Service Unavailable: Could not connect to HubSpot to fetch items. {e}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"HubSpot API error: {e.response.text}")

    results = response.json().get('results', [])
    for item_json in results:
        integration_item = _hubspot_contact_to_integration_item(item_json)
        list_of_integration_items.append(integration_item)
    
    print(f"Fetched HubSpot Items: {[item.__dict__ for item in list_of_integration_items]}")
    
    return list_of_integration_items