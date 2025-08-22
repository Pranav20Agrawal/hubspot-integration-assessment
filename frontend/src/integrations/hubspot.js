// frontend/src/integrations/hubspot.js
// HubSpot Integration Component: Handles the OAuth connection flow.

import { useState, useEffect } from 'react';
import { Box, Button, CircularProgress } from '@mui/material';
import axios from 'axios';

/**
 * A React component that renders a button to handle the HubSpot OAuth 2.0 flow.
 * @param {object} props - The component props.
 * @param {string} props.user - The current user's ID, used for state management.
 * @param {string} props.org - The current organization's ID, used for state management.
 * @param {object} props.integrationParams - An object holding integration-specific data.
 * @param {function} props.setIntegrationParams - A state setter to update the parent form's data.
 */
export const HubspotIntegration = ({ user, org, integrationParams, setIntegrationParams }) => {
    // Manages if the integration is currently connected (i.e., if valid credentials exist).
    const [isConnected, setIsConnected] = useState(false);
    // Manages the loading spinner state while the OAuth popup is open.
    const [isConnecting, setIsConnecting] = useState(false);

    /**
     * Initiates the HubSpot OAuth flow when the user clicks "Connect".
     * 1. Calls the backend to get a unique authorization URL.
     * 2. Opens that URL in a popup window for the user to approve permissions.
     * 3. Sets up an interval to check when the popup window is closed.
     */
    const handleConnectClick = async () => {
        try {
            setIsConnecting(true);
            const formData = new FormData();
            formData.append('user_id', user);
            formData.append('org_id', org);
            
            const response = await axios.post(`http://localhost:8000/integrations/hubspot/authorize`, formData);
            const authURL = response?.data;

            const newWindow = window.open(authURL, 'HubSpot Authorization', 'width=600, height=800');

            const pollTimer = window.setInterval(() => {
                if (newWindow?.closed) { 
                    window.clearInterval(pollTimer);
                    handleWindowClosed();
                }
            }, 200);
        } catch (e) {
            setIsConnecting(false);
            alert(e?.response?.data?.detail || 'An unknown error occurred.');
        }
    }

    /**
     * Called after the OAuth popup window is closed.
     * This function checks the backend to see if credentials were successfully created
     * during the OAuth flow and updates the component's state accordingly.
     */
    const handleWindowClosed = async () => {
        try {
            const formData = new FormData();
            formData.append('user_id', user);
            formData.append('org_id', org);

            const response = await axios.post(`http://localhost:8000/integrations/hubspot/credentials`, formData);
            const credentials = response.data; 
            
            if (credentials) {
                setIsConnected(true);
                setIntegrationParams(prev => ({ ...prev, credentials, type: 'HubSpot' }));
            }
        } catch (e) {
            // This error is expected if the user closes the popup without completing authentication.
            console.log("Authentication flow was not completed.");
        } finally {
            setIsConnecting(false);
        }
    }

    // On initial render, check if HubSpot credentials already exist and set the button state.
    useEffect(() => {
        const hasCredentials = integrationParams?.credentials && integrationParams?.type === 'HubSpot';
        setIsConnected(hasCredentials);
    }, [integrationParams]);

    return (
        <Box sx={{mt: 2, width: 300}}>
            Parameters
            <Box display='flex' alignItems='center' justifyContent='center' sx={{mt: 2}}>
                <Button 
                    variant='contained' 
                    onClick={isConnected ? undefined : handleConnectClick}
                    color={isConnected ? 'success' : 'primary'}
                    disabled={isConnecting}
                    fullWidth
                    style={{
                        cursor: isConnected ? 'default' : 'pointer',
                    }}
                >
                    {isConnected ? 'HubSpot Connected' : isConnecting ? <CircularProgress size={24} color="inherit" /> : 'Connect to HubSpot'}
                </Button>
            </Box>
        </Box>
    );
}