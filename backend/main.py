# main.py
"""
Main FastAPI application file.
This file initializes the FastAPI app, configures CORS, and defines all API routes
for the different integrations.
"""

from fastapi import FastAPI, Form, Request
from fastapi.middleware.cors import CORSMiddleware

from integrations.airtable import authorize_airtable, get_items_airtable, oauth2callback_airtable, get_airtable_credentials
from integrations.notion import authorize_notion, get_items_notion, oauth2callback_notion, get_notion_credentials
from integrations.hubspot import authorize_hubspot, get_hubspot_credentials, get_items_hubspot, oauth2callback_hubspot

app = FastAPI()

# Configure CORS (Cross-Origin Resource Sharing) to allow the frontend
# at localhost:3000 to communicate with this backend at localhost:8000.
origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === General Endpoints ===

@app.get('/')
def read_root():
    """A simple health check endpoint to confirm the server is running."""
    return {'Ping': 'Pong'}


# === Airtable Integration Endpoints ===

@app.post('/integrations/airtable/authorize')
async def authorize_airtable_integration(user_id: str = Form(...), org_id: str = Form(...)):
    """Initiates the Airtable OAuth2 authorization flow."""
    return await authorize_airtable(user_id, org_id)

@app.get('/integrations/airtable/oauth2callback')
async def oauth2callback_airtable_integration(request: Request):
    """Handles the OAuth2 callback from Airtable."""
    return await oauth2callback_airtable(request)

@app.post('/integrations/airtable/credentials')
async def get_airtable_credentials_integration(user_id: str = Form(...), org_id: str = Form(...)):
    """Retrieves stored Airtable credentials for the user."""
    return await get_airtable_credentials(user_id, org_id)

@app.post('/integrations/airtable/load')
async def get_airtable_items(credentials: str = Form(...)):
    """Loads items from Airtable using the provided credentials."""
    return await get_items_airtable(credentials)


# === Notion Integration Endpoints ===

@app.post('/integrations/notion/authorize')
async def authorize_notion_integration(user_id: str = Form(...), org_id: str = Form(...)):
    """Initiates the Notion OAuth2 authorization flow."""
    return await authorize_notion(user_id, org_id)

@app.get('/integrations/notion/oauth2callback')
async def oauth2callback_notion_integration(request: Request):
    """Handles the OAuth2 callback from Notion."""
    return await oauth2callback_notion(request)

@app.post('/integrations/notion/credentials')
async def get_notion_credentials_integration(user_id: str = Form(...), org_id: str = Form(...)):
    """Retrieves stored Notion credentials for the user."""
    return await get_notion_credentials(user_id, org_id)

@app.post('/integrations/notion/load')
async def get_notion_items(credentials: str = Form(...)):
    """Loads items from Notion using the provided credentials."""
    return await get_items_notion(credentials)


# === HubSpot Integration Endpoints ===

@app.post('/integrations/hubspot/authorize')
async def authorize_hubspot_integration(user_id: str = Form(...), org_id: str = Form(...)):
    """Initiates the HubSpot OAuth2 authorization flow."""
    return await authorize_hubspot(user_id, org_id)

@app.get('/integrations/hubspot/oauth2callback')
async def oauth2callback_hubspot_integration(request: Request):
    """Handles the OAuth2 callback from HubSpot."""
    return await oauth2callback_hubspot(request)

@app.post('/integrations/hubspot/credentials')
async def get_hubspot_credentials_integration(user_id: str = Form(...), org_id: str = Form(...)):
    """Retrieves stored HubSpot credentials for the user."""
    return await get_hubspot_credentials(user_id, org_id)

@app.post('/integrations/hubspot/load')
async def get_hubspot_items_integration(credentials: str = Form(...)):
    """Loads items from HubSpot using the provided credentials."""
    return await get_items_hubspot(credentials)